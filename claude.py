import xmlrpc.client
import base64
import logging

class OdooProductMigrator:
    def __init__(self, source_url, source_db, source_username, source_password,
                 target_url, target_db, target_username, target_password):
        """
        Initialize the Odoo Product Migrator with source and target server credentials.
        
        :param source_url: URL of the source Odoo server
        :param source_db: Database name of the source server
        :param source_username: Username for the source server
        :param source_password: Password for the source server
        :param target_url: URL of the target Odoo server
        :param target_db: Database name of the target server
        :param target_username: Username for the target server
        :param target_password: Password for the target server
        """
        # Source server connection
        self.source_common = xmlrpc.client.ServerProxy(f'{source_url}/xmlrpc/2/common')
        self.source_uid = self.source_common.authenticate(source_db, source_username, source_password, {})
        self.source_models = xmlrpc.client.ServerProxy(f'{source_url}/xmlrpc/2/object')
        self.source_db = source_db
        self.source_username = source_username
        self.source_password = source_password

        # Target server connection
        self.target_common = xmlrpc.client.ServerProxy(f'{target_url}/xmlrpc/2/common')
        self.target_uid = self.target_common.authenticate(target_db, target_username, target_password, {})
        self.target_models = xmlrpc.client.ServerProxy(f'{target_url}/xmlrpc/2/object')
        self.target_db = target_db
        self.target_username = target_username
        self.target_password = target_password

        # Setup logging
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def _migrate_documents(self, product_id, source_product_id):
        """
        Migrate all document attachments for a specific product.
        
        :param product_id: New product ID in target system
        :param source_product_id: Original product ID in source system
        :return: List of new document IDs
        """
        # Expand search to include multiple document-related models
        document_models = [
            'ir.attachment',
            'documents.document'  # Additional document model
        ]
        
        new_document_ids = []
        
        for doc_model in document_models:
            try:
                # Search for documents linked to the product
                document_domain = [
                    '|',  # OR condition
                    ('res_model', '=', 'product.product'),
                    ('res_model', '=', 'product.template'),
                    ('res_id', '=', source_product_id)
                ]
                
                # Read documents from source
                documents = self.source_models.execute_kw(
                    self.source_db, self.source_uid, self.source_password,
                    doc_model, 'search_read', 
                    [document_domain], 
                    {'fields': ['name', 'datas', 'mimetype', 'type', 'res_model', 'description']}
                )
                
                # Migrate each document
                for doc in documents:
                    try:
                        # Prepare document data for migration
                        doc_data = {
                            'name': doc.get('name', 'Unnamed Document'),
                            'datas': doc.get('datas', False),
                            'mimetype': doc.get('mimetype', False),
                            'type': doc.get('type', 'binary'),
                            'res_model': 'product.product',
                            'res_id': product_id,
                            'description': doc.get('description', False)
                        }
                        
                        # Create document in target system
                        new_doc_id = self.target_models.execute_kw(
                            self.target_db, self.target_uid, self.target_password,
                            doc_model, 'create', [doc_data]
                        )
                        
                        new_document_ids.append(new_doc_id)
                        self.logger.info(f"Migrated document: {doc.get('name', 'Unnamed')}")
                    
                    except Exception as doc_error:
                        self.logger.error(f"Failed to migrate individual document: {str(doc_error)}")
            
            except Exception as model_error:
                self.logger.error(f"Error processing {doc_model} documents: {str(model_error)}")
        
        return new_document_ids

    def migrate_products(self, product_ids=None, domain=None):
        """
        Migrate products from source to target Odoo server.
        
        :param product_ids: Optional list of specific product IDs to migrate
        :param domain: Optional domain to filter products
        :return: Mapping of source to target product IDs
        """
        # Prepare domain for product search
        if not product_ids and not domain:
            domain = []
        elif product_ids:
            domain = [('id', 'in', product_ids)]
        
        # Retrieve products from source server
        products = self.source_models.execute_kw(
            self.source_db, self.source_uid, self.source_password,
            'product.product', 'search_read', 
            [domain], 
            {'fields': [
                'name', 'default_code', 'barcode', 'type', 'categ_id', 
                'lst_price', 'standard_price', 'description', 
                'description_sale', 'image_1920'
            ]}
        )
        
        # Product migration tracking
        product_id_map = {}
        
        for product in products:
            try:
                # Prepare product data for migration
                product_data = {
                    'name': product['name'],
                    'default_code': product.get('default_code', False),
                    'barcode': product.get('barcode', False),
                    'type': product['type'],
                    'categ_id': self._map_category(product['categ_id'][0]) if product.get('categ_id') else False,
                    'lst_price': product.get('lst_price', 0.0),
                    'standard_price': product.get('standard_price', 0.0),
                    'description': product.get('description', False),
                    'description_sale': product.get('description_sale', False),
                }
                
                # Handle product image
                if product.get('image_1920'):
                    product_data['image_1920'] = product['image_1920']
                
                # Create product in target system
                new_product_id = self.target_models.execute_kw(
                    self.target_db, self.target_uid, self.target_password,
                    'product.product', 'create', [product_data]
                )
                
                # Track product ID mapping
                product_id_map[product['id']] = new_product_id
                
                # Migrate documents (including attachments)
                self._migrate_documents(new_product_id, product['id'])
                
                self.logger.info(f"Migrated product: {product['name']}")
            
            except Exception as e:
                self.logger.error(f"Failed to migrate product {product['name']}: {str(e)}")
        
        return product_id_map

    def _map_category(self, source_category_id):
        """
        Map product category from source to target system.
        This is a simplified method and might need customization.
        
        :param source_category_id: Category ID from source system
        :return: Corresponding category ID in target system
        """
        # Retrieve category from source
        source_category = self.source_models.execute_kw(
            self.source_db, self.source_uid, self.source_password,
            'product.category', 'read', 
            [source_category_id], 
            {'fields': ['name', 'parent_id']}
        )[0]
        
        # Try to find or create corresponding category in target
        target_category_domain = [('name', '=', source_category['name'])]
        if source_category.get('parent_id'):
            parent_category_id = self._map_category(source_category['parent_id'][0])
            target_category_domain.append(('parent_id', '=', parent_category_id))
        
        target_category_ids = self.target_models.execute_kw(
            self.target_db, self.target_uid, self.target_password,
            'product.category', 'search', 
            [target_category_domain]
        )
        
        if target_category_ids:
            return target_category_ids[0]
        
        # Create category if not exists
        new_category_data = {
            'name': source_category['name'],
            'parent_id': self._map_category(source_category['parent_id'][0]) if source_category.get('parent_id') else False
        }
        
        return self.target_models.execute_kw(
            self.target_db, self.target_uid, self.target_password,
            'product.category', 'create', 
            [new_category_data]
        )

# Example Usage
if __name__ == '__main__':
    migrator = OdooProductMigrator(
        source_url='http://localhost:8010/',
        source_db='odoo',
        source_username='ask@ascendingtech.biz',
        source_password='donthack',
        target_url='http://localhost:8030/',
        target_db='odoo',
        target_username='ask@ascendingtech.biz',
        target_password='donthack'
    )
    
    # Migrate all products
    migrator.migrate_products()