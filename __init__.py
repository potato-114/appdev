from flask import Flask, render_template, request, redirect, url_for, send_file
from Forms import CreateItemForm
import shelve, Item
import pandas as pd
from io import BytesIO

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')



@app.route('/createItem', methods=['GET', 'POST'])
def create_item():
    create_item_form = CreateItemForm(request.form)
    if request.method == 'POST' and create_item_form.validate():
        items_dict = {}
        db = shelve.open('item.db', 'c')

        try:
            items_dict = db['Items']
            Item.Item.count_id = db['ItemCount']
        except:
            print("Error in retrieving Items from item.db.")

        item = Item.Item(create_item_form.category.data, create_item_form.item.data, create_item_form.description.data,
                         create_item_form.condition.data, create_item_form.stock.data, create_item_form.selling_price.data)

        items_dict[item.get_item_id()] = item

        db['Items'] = items_dict
        db['ItemCount'] = Item.Item.count_id

        db.close()

        return redirect(url_for('retrieve_items'))
    return render_template('createItem.html', form=create_item_form)



@app.route('/retrieveItems')
def retrieve_items():
    items_dict = {}
    db = shelve.open('item.db', 'r')
    items_dict = db['Items']
    db.close()

    items_list = []
    for key in items_dict:
        item = items_dict.get(key)
        items_list.append(item)

    return render_template('retrieveItems.html', count=len(items_list), items_list=items_list)



@app.route('/updateItem/<int:id>/', methods=['GET', 'POST'])
def update_item(id):
    update_item_form = CreateItemForm(request.form)
    if request.method == 'POST' and update_item_form.validate():
        items_dict = {}
        db = shelve.open('item.db', 'w')
        items_dict = db['Items']

        item = items_dict.get(id)
        item.set_category(update_item_form.category.data)
        item.set_item(update_item_form.item.data)
        item.set_description(update_item_form.description.data)
        item.set_condition(update_item_form.condition.data)
        item.set_stock(update_item_form.stock.data)
        item.set_selling_price(update_item_form.selling_price.data)

        db['Items'] = items_dict
        db.close()

        return redirect(url_for('retrieve_items'))
    else:
        items_dict = {}
        db = shelve.open('item.db', 'r')
        items_dict = db['Items']
        db.close()

        item = items_dict.get(id)
        update_item_form.category.data = item.get_category()
        update_item_form.item.data = item.get_item()
        update_item_form.description.data = item.get_description()
        update_item_form.condition.data = item.get_condition()
        update_item_form.stock.data = item.get_stock()
        update_item_form.selling_price.data = item.get_selling_price()

        return render_template('updateItem.html', form=update_item_form)



@app.route('/deleteItem/<int:id>', methods=['POST'])
def delete_item(id):
    items_dict = {}
    db = shelve.open('item.db', 'w')
    items_dict = db['Items']

    items_dict.pop(id)

    db['Items'] = items_dict
    db.close()

    return redirect(url_for('retrieve_items'))



@app.route('/exportTable', methods=['GET'])
def export_table():
    export_format = request.args.get('format', 'xlsx')

    items_dict = {}
    db = shelve.open('item.db', 'c')
    items_dict = db.get('Items', {})
    db.close()
    # data to export is stored in the 'Items' key

    items_list = []
    for key in items_dict:
        item = items_dict.get(key)
        item_data = {
            'ID': item.get_item_id(),
            'Category': item.get_category(),
            'Item': item.get_item(),
            'Description': item.get_description(),
            'Condition': item.get_condition(),
            'Stock': item.get_stock(),
            'Selling Price ($)': item.get_selling_price()
        }
        items_list.append(item_data)

    # convert data to pandas dataframe
    df = pd.DataFrame(items_list)

    # creates in-memory buffer to store file
    output = BytesIO()

    if export_format == 'xlsx':
        # export dataframe to excel (.xlsx) format using openpyxl engine
        df.to_excel(output, index=False, engine='openpyxl')
        # reset buffer position to beginning
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name='table.xlsx')

    elif export_format == 'xls':
        df.to_excel(output, index=False, engine='xlsxwriter')
        output.seek(0)
        return send_file(output, mimetype='application/vnd.ms-excel', as_attachment=True, download_name='table.xls')

    elif export_format == 'csv':
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name='table.csv')

    else:
        # return error if the format is unsupported
        return 'Unsupported format', 400



if __name__ == '__main__':
    app.run()
