import xmlrpc.client
# Odoo credentials
source_url = "http://localhost:8010/"  # Replace with your Odoo server URL
source_db  = "odoo"            # Replace with your database name
source_username  = "ask@ascendingtech.biz"           # Replace with your login username
source_password  = "donthack"           # Replace with your password

# Target Odoo Credentials
target_url = "http://localhost:8030/"
target_db = "odoo"
target_username = "ask@ascendingtech.biz"
target_password = "donthack"


# Connect to source Odoo
source_common = xmlrpc.client.ServerProxy(f"{source_url}/xmlrpc/2/common")
source_uid = source_common.authenticate(source_db, source_username, source_password, {})
source_models = xmlrpc.client.ServerProxy(f"{source_url}/xmlrpc/2/object")

# Connect to target Odoo
target_common = xmlrpc.client.ServerProxy(f"{target_url}/xmlrpc/2/common")
target_uid = target_common.authenticate(target_db, target_username, target_password, {})
target_models = xmlrpc.client.ServerProxy(f"{target_url}/xmlrpc/2/object")

# Step 1: Fetch products from the source Odoo
products = source_models.execute_kw(
    source_db, source_uid, source_password,
    'product.product', 'search_read',
    [[]],  # No filters, fetch all products
    {'fields': ['id', 'name', 'list_price', 'default_code', 'categ_id'], 'limit': 1000}  # Adjust fields as needed
)

print(f"Found {len(products)} products in the source system.")

# Step 2: Fetch documents (attachments) associated with each product
for product in products:
    product_id = product['id']
    product_attachments = source_models.execute_kw(
        source_db, source_uid, source_password,
        'ir.attachment', 'search_read',
        [[('res_model', '=', 'product.product'), ('res_id', '=', product_id)]],  # Attachments linked to the product
        {'fields': ['name', 'datas', 'res_id']}
    )

    # Step 3: Create the product in the target Odoo
    new_product_id = target_models.execute_kw(
        target_db, target_uid, target_password,
        'product.product', 'create',
        [{
            'name': product['name'],
            'list_price': product['list_price'],
            'default_code': product['default_code'],
            'categ_id': product['categ_id'] and product['categ_id'][0] or False  # Handle many2one field
        }]
    )
    print(f"Created product {product['name']} with ID {new_product_id} in the target system.")
