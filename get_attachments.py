import xmlrpc.client
import base64

# Odoo credentials
source_url = "http://localhost:8010/"
source_db = "odoo"
source_username = "ask@ascendingtech.biz"
source_password = "donthack"

# Target Odoo Credentials
target_url = "http://localhost:8030/"
target_db = "odoo"
target_username = "ask@ascendingtech.biz"
target_password = "donthack"

# Authenticate with Source Odoo
source_common = xmlrpc.client.ServerProxy(f"{source_url}/xmlrpc/2/common")
source_uid = source_common.authenticate(source_db, source_username, source_password, {})

# Authenticate with Target Odoo
target_common = xmlrpc.client.ServerProxy(f"{target_url}/xmlrpc/2/common")
target_uid = target_common.authenticate(target_db, target_username, target_password, {})

if not source_uid or not target_uid:
    raise Exception("Authentication failed for one or both servers.")

print("Authenticated successfully with both servers.")

# Object proxies
source_models = xmlrpc.client.ServerProxy(f"{source_url}/xmlrpc/2/object")
target_models = xmlrpc.client.ServerProxy(f"{target_url}/xmlrpc/2/object")

# Step 1: Fetch product templates and their data from source server
print("Fetching products from source...")
# Fetch products and their images from product.product
product_data = source_models.execute_kw(
    source_db, source_uid, source_password,
    'product.product', 'search_read',
    [[]],  # No filters, fetch all products
    {'fields': ['id', 'name', 'image_1920']}
)

for product in product_data:
    product_name = product['name']
    product_image = product.get('image_1920')

    # Create product in target Odoo with image_1920
    new_product_data = {'name': product_name}
    if product_image:
        new_product_data['image_1920'] = product_image  # Base64-encoded image

    new_product_id = target_models.execute_kw(
        target_db, target_uid, target_password,
        'product.product', 'create',
        [new_product_data]
    )
    print(f"Created product '{product_name}' with ID {new_product_id} on target server.")

# Step 3: Fetch Attachments from ir.attachment for product.template
print("\nFetching product attachments...")
product_templates = source_models.execute_kw(
    source_db, source_uid, source_password,
    'product.template', 'search_read',
    [[]],  # Fetch all product templates
    {'fields': ['id', 'name']}
)

for template in product_templates:
    template_id = template['id']
    template_name = template['name']

    # Fetch attachments for this product.template
    attachments = source_models.execute_kw(
        source_db, source_uid, source_password,
        'ir.attachment', 'search_read',
        [[['res_model', '=', 'product.template'], ['res_id', '=', template_id]]],
        {'fields': ['name', 'datas', 'mimetype']}
    )

    # Step 4: Upload Attachments to Target Odoo
    for attachment in attachments:
        attachment_name = attachment['name']
        attachment_data = attachment.get('datas')
        attachment_mimetype = attachment.get('mimetype', 'application/octet-stream')

        if attachment_data:
            target_models.execute_kw(
                target_db, target_uid, target_password,
                'ir.attachment', 'create',
                [{
                    'name': attachment_name,
                    'datas': attachment_data,  # Base64-encoded data
                    'mimetype': attachment_mimetype,
                    'res_model': 'product.template',
                    'res_id': template_id,  # Link to the target product.template
                }]
            )
            print(f"Uploaded attachment '{attachment_name}' for product '{template_name}'.")
        else:
            print(f"No data for attachment '{attachment_name}' in product '{template_name}'.")

print("\nMigration complete! 🚀")



# source_products = source_models.execute_kw(
#     source_db, source_uid, source_password,
#     'product.template', 'search_read',
#     [[]],  # Add filters if needed
#     {'fields': ['name', 'type', 'list_price', 'default_code', 'description']}  # Fields to migrate
# )

# print(f"Fetched {len(source_products)} products.")

# # Step 2: Migrate products to target server and store new IDs
# product_mapping = {}  # To map old template IDs to new ones
# for product in source_products:
#     # Prepare product data, including image_1920
#     product_data = {
#         'name': product['name'],
#         'type': product['type'],
#         'list_price': product['list_price'],
#         'default_code': product['default_code'],
#         'description': product['description'],
#     }

#     # Include product icon if available
#     if product.get('image_1920'):
#         product_data['image_1920'] = product['image_1920']
#         print(f"Including icon for product: {product['name']}")

#     # Create product in the target server
#     new_product_id = target_models.execute_kw(
#         target_db, target_uid, target_password,
#         'product.template', 'create',
#         [product_data]
#     )
#     product_mapping[product['id']] = new_product_id
#     print(f"Migrated product: {product['name']} (New ID: {new_product_id})")

# # Step 3: Fetch and migrate attachments for each product
# print("Migrating attachments...")
# for old_product_id, new_product_id in product_mapping.items():
#     # Fetch attachments linked to the old product.template
#     attachments = source_models.execute_kw(
#         source_db, source_uid, source_password,
#         'ir.attachment', 'search_read',
#         [[('res_model', '=', 'product.template'), ('res_id', '=', old_product_id)]],
#         {'fields': ['name', 'datas', 'mimetype']}
#     )

#     # Upload attachments to the target server
#     for attachment in attachments:
#         if attachment['datas']:  # Check if attachment has data
#             target_models.execute_kw(
#                 target_db, target_uid, target_password,
#                 'ir.attachment', 'create',
#                 [{
#                     'name': attachment['name'],
#                     'res_model': 'product.template',
#                     'res_id': new_product_id,  # Link to the new product ID
#                     'datas': attachment['datas'],  # Base64-encoded file data
#                     'mimetype': attachment['mimetype']
#                 }]
#             )
#             print(f"Uploaded attachment: {attachment['name']} for product ID {new_product_id}")

# print("Migration completed successfully.")