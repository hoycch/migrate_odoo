
import xmlrpc.client
import base64
import csv

# Odoo credentials
source_url = "http://localhost:8010/"
source_db = "odoo"
source_username = "ask@ascendingtech.biz"
source_password = "donthack"

# Authenticate with Source Odoo
source_common = xmlrpc.client.ServerProxy(f"{source_url}/xmlrpc/2/common")
source_uid = source_common.authenticate(source_db, source_username, source_password, {})
source_models = xmlrpc.client.ServerProxy(f"{source_url}/xmlrpc/2/object")

fields = source_models.execute_kw(
    source_db, source_uid, source_password,
    'product.product', 'fields_get',
    [], {'attributes': ['string', 'type', 'relation']}
)

# Prepare the CSV file
with open('product_string.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    # Write the header
    writer.writerow(['Field Name', 'Related Model', 'Field Type', 'Field Label'])

    # Loop through the fields and write relational fields to the CSV
    for field_name, field_data in fields.items():
        if 'string' in field_data:  # Check if the field is relational
            writer.writerow([
                field_name,                     # Field Name
                # field_data['relation'],         # Related Model
                field_data.get('type', ''),     # Field Type (e.g., many2one, many2many)
                field_data.get('string', '')    # Field Label (human-readable name)
            ])

print("Relational fields exported to 'relational_fields.csv'")