python manage.py shell
# Step 1: 导入模型
from restaurant.models import Category, Boisson


# Step 2: 创建新的分类
cocktail_sa = Category(name='COCKTAILS SA')
cocktail_sa.save()

cocktail_aa = Category(name='COCKTAILS AA')
cocktail_aa.save()

eaux = Category(name='EAUX')
eaux.save()

coffees_teas = Category(name='Coffees and Teas')
coffees_teas.save()

digestives = Category(name='Digestives')
digestives.save()

# Step 3: 创建饮料并指定分类
# EAUX 类别饮料
drinks_eaux = [
    ("Carola rouge pétillante 50cl", 3.50),
    ("Carola rouge pétillante 1L", 5.00),
    ("Carola verte légèrement pétillante 50cl", 3.50),
    ("Carola verte légèrement pétillante 1L", 5.00),
    ("Carola bleue nature 50cl", 3.50),
    ("Carola bleue nature 1L", 5.00)
]

for name, price in drinks_eaux:
    drink = Boisson(name=name, prix=price, category=eaux)
    drink.save()

# Coffees and Teas 类别饮料
drinks_coffees_teas = [
    ("Café", 2.00),
    ("Décaféiné", 2.00),
    ("Café rallongé, au lait", 2.50),
    ("Double expresso", 3.80),
    ("Café crème", 2.50),
    ("Cappuccino", 3.70),
    ("Irish Coffee", 8.50),
    ("Thé au jasmin", 2.50),
    ("Thé vert", 2.50),
    ("Thé à la menthe", 2.50),
    ("Thé aux fruits rouges", 2.50),
    ("Infusions", 2.50),
    ("Thé tilleul", 2.50),
    ("Thé verveine", 2.50)
]

for name, price in drinks_coffees_teas:
    drink = Boisson(name=name, prix=price, category=coffees_teas)
    drink.save()

# Digestives 类别饮料
drinks_digestives = [
    ("Mei Kwei Lu (Alcool de riz)", 3.50),
    ("Cognac Rémy Martin fine VSOP", 8.50),
    ("Poire Williams", 6.50),
    ("Liqueur de framboise", 6.50),
    ("Marc de Gewurztraminer", 6.50),
    ("Cointreau", 6.50),
    ("Grand Marnier", 6.50),
    ("Calvados", 6.50)
]

for name, price in drinks_digestives:
    drink = Boisson(name=name, prix=price, category=digestives)
    drink.save()
    
drinks_sa = [
    ("Virgin Mojito", 5.5),
    ("Cocolada", 5.5),
    ("Magic Amazon", 5.5),
    ("Passion Tropic", 5.5),
    ("Royal Blue", 5.5),
    ("Sand Island", 5.5)
]

for name, price in drinks_sa:
    drink = Boisson(name=name, prix=price, category=cocktail_sa)
    drink.save()

drinks_aa = [
    ("Mojito", 6.0),
    ("Pina Colada", 6.0),
    ("Mai Tai", 6.0),
    ("Swimming Pool", 6.0),
    ("Zombie", 6.0),
    ("T Sunrise", 6.0),
    ("Pekin Express", 6.0),
    ("Sex on the Beach", 6.0)
]

for name, price in drinks_aa:
    drink = Boisson(name=name, prix=price, category=cocktail_aa)
    drink.save()