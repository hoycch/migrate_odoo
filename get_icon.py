import xmlrpc.client

src_url = "http://localhost:8010/"
src_db = "odoo"
src_username = "ask@ascendingtech.biz"
src_password = "donthack"

src_common = xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(src_url))
src_models = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(src_url))

src_uid = src_common.authenticate(src_db, src_username, src_password, {})

tgt_url = "http://localhost:8030/"
tgt_db = "odoo"
tgt_username = "ask@ascendingtech.biz"
tgt_password = "donthack"

tgt_common = xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(tgt_url))
tgt_models = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(tgt_url))

tgt_uid = tgt_common.authenticate(tgt_db, tgt_username, tgt_password, {})

products = src_models.execute_kw(src_db, src_uid, src_password, 'product.product', 'search_read', [[]], {'fields': ['name', 'description', 'image_1920']})
for product in products:
    product_id = tgt_models.execute_kw(tgt_db, tgt_uid, tgt_password, 'product.product', 'create', [{
        'name': product['name'],
        'description': product['description'],
        'image_1920': product['image_1920'],  # base64 encoded image
    }])