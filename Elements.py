import requests
import pymysql


class API:
    """Communicate with API"""
    def __init__(self):
        self.json = None

    def communication_api(self, url):
        self.r = requests.get(url)
        self.json = self.r.json()


class Display:
    """display info from BDD when user take a choice"""

    def __init__(self):
        self.list_pos = ("yes", "y", "oui")
        self.list_neg = ("no", "n", "non")

    def disp_info_cat(self, bdd):
        with bdd.connection.cursor() as cursor:
            try:
                sql = "SELECT * FROM categorie"
                cursor.execute(sql)
                result = cursor.fetchall()
                return(result)
            except Exception as e:
                print(e)

    def disp_info_prod(self, bdd, user_input):
        with bdd.connection.cursor() as cursor:
            try:
                sql = "SELECT id, nom, nutriscore, ingredient, magasin, url FROM produit WHERE categorie = '{0}'"\
                    .format(user_input)
                cursor.execute(sql)
                result = cursor.fetchall()
                return result
            except Exception as e:
                print(e)

    def sel_alt_prod(self, bdd, user_input_cat, user_input_prod):
        """select 5 different's products with nutriscore smaller than the user's choice"""
        with bdd.connection.cursor() as cursor:
            try:
                sql = "SELECT id, nom, nutriscore FROM produit WHERE categorie = '{0}' \
                AND nutriscore < (SELECT nutriscore FROM produit WHERE id = '{1}') LIMIT 5"\
                .format(user_input_cat, user_input_prod)
                cursor.execute(sql)
                result = cursor.fetchall()
                return result
            except Exception as e:
                print(e)

    def disp_favo(self, bdd):
        with bdd.connection.cursor() as cursor:
            try:
                sql = "SELECT * FROM produit WHERE id IN (SELECT id FROM favori)"
                cursor.execute(sql)
                result = cursor.fetchall()
                print(result)
            except Exception as e:
                print(e)


class MysqlBdd:
    """Allow to connect to mysql's bdd"""

    host = input("hostname :")
    user = input("user's name :")
    psw = input("password :")
    db = input("database's name :")

    connection = pymysql.connect(host=host,
                                 user=user,
                                 password=psw,
                                 db=db,
                                 charset='utf8mb4')

    def insert_fav(self, user_choice):
        with self.connection.cursor() as cursor:
            try:
                sql = "INSERT INTO favori(id) VALUES (%s)"
                cursor.execute(sql, user_choice)
            except pymysql.Error:
                print('This product already exist in your favories')
        self.connection.commit()


class Injection:
    """Inject data from api (json) to database"""
    def __init__(self):
        self.url = None
        self.LIMIT_PRODUCT = 100
        self.list_category = ["boissons", "snacks-sucres", "produits-laitiers"]
        self.info_products = None
        self.k = 0
        self.list_names_products = []

    def api_to_bdd(self, bdd, api):
        """for each categories name in list_category the method got 100 products from api
        then insert one by one into the database"""
        for i, category in enumerate(self.list_category):
            try:
                with bdd.connection.cursor() as cursor:
                    sql = "INSERT INTO categorie (nom) VALUES (%s)"
                    cursor.execute(sql, category)
            except Exception as e:
                print(e)
            bdd.connection.commit()

            self.url = 'https://fr.openfoodfacts.org/cgi/search.pl?action=process&tagtype_0=categories&tag_' \
                       'contains_0=contains&tag_0=' + category + '&sort_by=unique_scans_n&page' \
                       '_size=100&axis_x=energy&axis_y=products_n&action=display&json=1'
            api.communication_api(self.url)

            while self.k < self.LIMIT_PRODUCT:
                try:
                    self.info_products = (api.json['products'][self.k]['product_name'],
                                          api.json['products'][self.k]['ingredients_text_fr'],
                                          api.json['products'][self.k]['nutrition_grade_fr'],
                                          api.json['products'][self.k]['purchase_places'],
                                          api.json['products'][self.k]['url'])
                    if self.info_products[0].lower().strip() in self.list_names_products:
                        self.k += 1
                        continue
                    else:
                        self.list_names_products.append(self.info_products[0].lower().strip())
                except KeyError:
                    self.k += 1
                    continue

                try:
                    with bdd.connection.cursor() as cursor:
                        sql = "INSERT INTO produit(nom, ingredient, nutriscore" \
                              ", magasin, url, categorie) VALUES (%s, %s, %s, %s, %s, %s)"
                        id = str(i + 1)
                        cursor.execute(sql, (self.info_products[0], self.info_products[1], self.info_products[2],
                                             self.info_products[3], self.info_products[4], id))
                except pymysql.DatabaseError:
                    print("A duplicate name has been deleted")
                bdd.connection.commit()
                self.k += 1
            self.k = 0
