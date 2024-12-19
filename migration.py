import xmlrpc.client
import base64

# Source Odoo connection details
source_url = "http://localhost:8010/"
source_db = "odoo"
source_username = "ask@ascendingtech.biz"
source_password = "donthack"

# # Target Odoo connection details
# target_url = 'https://easy-equip-limited.odoo.com/'
# target_db = 'easy-equip-limited'
# target_username = 'hoycch@gmail.com'
# target_password = 'donthack'
# Target Odoo Credentials
target_url = "http://localhost:8030/"
target_db = "odoo"
target_username = "ask@ascendingtech.biz"
target_password = "donthack"

# Connect to Source and Target Odoo servers
def connect_odoo(url, db, username, password):
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    return uid, models

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
source_products = source_models.execute_kw(
    source_db, source_uid, source_password,
    'product.template', 'search_read',
    [[]],  # Add filters if needed
    {'fields': ['name', 'type', 'list_price', 'default_code', 'description']}  # Fields to migrate
)

print(f"Fetched {len(source_products)} products.")

# Step 2: Migrate products to target server and store new IDs
product_mapping = {}  # To map old template IDs to new ones
for product in source_products:
    # Prepare product data, including image_1920
    product_data = {
        'name': product['name'],
        'type': product['type'],
        'list_price': product['list_price'],
        'default_code': product['default_code'],
        'description': product['description'],
    }

    # Create product in the target server
    new_product_id = target_models.execute_kw(
        target_db, target_uid, target_password,
        'product.template', 'create',
        [product_data]
    )
    product_mapping[product['id']] = new_product_id
    print(f"Migrated product: {product['name']} (New ID: {new_product_id})")

# Step 3: Fetch and migrate attachments for each product
print("Migrating attachments...")
for old_product_id, new_product_id in product_mapping.items():
    # Fetch attachments linked to the old product.template
    attachments = source_models.execute_kw(
        source_db, source_uid, source_password,
        'ir.attachment', 'search_read',
        [[('res_model', '=', 'product.template'), ('res_id', '=', old_product_id)]],
        {'fields': ['name', 'datas', 'mimetype']}
    )

    # Upload attachments to the target server
    for attachment in attachments:
        if attachment['datas']:  # Check if attachment has data
            target_models.execute_kw(
                target_db, target_uid, target_password,
                'ir.attachment', 'create',
                [{
                    'name': attachment['name'],
                    'res_model': 'product.template',
                    'res_id': new_product_id,  # Link to the new product ID
                    'datas': attachment['datas'],  # Base64-encoded file data
                    'mimetype': attachment['mimetype']
                }]
            )
            print(f"Uploaded attachment: {attachment['name']} for product ID {new_product_id}")

print("Migration completed successfully.")