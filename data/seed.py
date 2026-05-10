"""
Comprehensive sample database for TestNucleus.

7 tables, ~250 rows, 40+ intentional data quality issues spread across
completeness, uniqueness, conformity, validity, and consistency categories.

Run from project root: python data/seed.py
"""
import sqlite3
from pathlib import Path


SCHEMA = """
DROP TABLE IF EXISTS review;
DROP TABLE IF EXISTS payment;
DROP TABLE IF EXISTS order_item;
DROP TABLE IF EXISTS "order";
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS category;

CREATE TABLE category (
    category_id  INTEGER PRIMARY KEY,
    name         VARCHAR(50) NOT NULL,
    description  TEXT
);

CREATE TABLE customer (
    customer_id  INTEGER PRIMARY KEY,
    first_name   VARCHAR(50),
    last_name    VARCHAR(50),
    email        VARCHAR(100),
    phone_number VARCHAR(20),
    country      VARCHAR(50),
    created_date DATE
);

CREATE TABLE product (
    product_id     INTEGER PRIMARY KEY,
    product_name   VARCHAR(100),
    category_id    INTEGER,
    price          DECIMAL(10,2),
    stock_quantity INTEGER,
    sku            VARCHAR(20),
    FOREIGN KEY (category_id) REFERENCES category(category_id)
);

CREATE TABLE "order" (
    order_id         INTEGER PRIMARY KEY,
    customer_id      INTEGER,
    order_date       DATE,
    total_amount     DECIMAL(10,2),
    shipping_address VARCHAR(255),
    status           VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
);

CREATE TABLE order_item (
    item_id    INTEGER PRIMARY KEY,
    order_id   INTEGER,
    product_id INTEGER,
    quantity   INTEGER,
    unit_price DECIMAL(10,2),
    FOREIGN KEY (order_id)   REFERENCES "order"(order_id),
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);

CREATE TABLE payment (
    payment_id     INTEGER PRIMARY KEY,
    order_id       INTEGER,
    payment_date   DATE,
    amount         DECIMAL(10,2),
    payment_method VARCHAR(30),
    status         VARCHAR(20),
    FOREIGN KEY (order_id) REFERENCES "order"(order_id)
);

CREATE TABLE review (
    review_id   INTEGER PRIMARY KEY,
    customer_id INTEGER,
    product_id  INTEGER,
    rating      INTEGER,
    review_text TEXT,
    review_date DATE,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    FOREIGN KEY (product_id)  REFERENCES product(product_id)
);
"""

# ---------------------------------------------------------------------------
# Reference data — clean, used for referential integrity checks
# ---------------------------------------------------------------------------
CATEGORIES = [
    # (category_id, name, description)
    (1,  "Electronics",   "Consumer electronic devices and gadgets"),
    (2,  "Accessories",   "Device accessories and add-ons"),
    (3,  "Audio",         "Speakers, headphones, and audio equipment"),
    (4,  "Smart Home",    "Home automation and smart devices"),
    (5,  "Wearables",     "Smartwatches, fitness trackers, and wearables"),
    (6,  "Gaming",        "Gaming peripherals and accessories"),
    (7,  "Photography",   "Cameras, lenses, and photography gear"),
    (8,  "Networking",    "Routers, switches, and networking equipment"),
    (9,  "Storage",       "Hard drives, SSDs, and storage solutions"),
    (10, "Office",        "Office supplies and desk accessories"),
]

# ---------------------------------------------------------------------------
# Customers — 30 rows
# Issues: 3 null emails, 3 invalid emails, 2 trailing spaces, 1 duplicate
#         email, 3 null phones, 2 invalid phones, 1 first_name > 50 chars
# ---------------------------------------------------------------------------
CUSTOMERS = [
    # (customer_id, first_name, last_name, email, phone_number, country, created_date)
    # --- Valid records ---
    (1,  "James",     "Wilson",    "james.wilson@gmail.com",             "+1-202-555-0101",  "USA",          "2022-01-15"),
    (2,  "Sarah",     "Chen",      "sarah.chen@yahoo.com",               "+1-415-555-0182",  "USA",          "2022-02-03"),
    (3,  "Mohammed",  "Al-Rashid", "m.alrashid@outlook.com",             None,               "UK",           "2022-02-14"),  # null phone (nullable field)
    (4,  "Emily",     "Rodriguez", "emily.r@company.com",                "+44-20-7946-0958", "UK",           "2022-03-01"),
    (6,  "Priya",     "Patel",     "priya.patel@email.com",              None,               "India",        "2022-03-20"),  # null phone
    (7,  "David",     "Kim",       "david.kim@techcorp.io",              "+82-10-1234-5678", "South Korea",  "2022-04-05"),
    (10, "Anna",      "Kowalski",  "anna.k@poland.eu",                   "+48-22-123-4567",  "Poland",       "2022-05-15"),
    (11, "Carlos",    "Mendez",    "carlos.mendez@hotmail.com",          "+52-55-1234-5678", "Mexico",       "2022-06-01"),
    (13, "Wei",       "Zhang",     "wei.zhang@163.com",                  "+86-138-0000-1234","China",        "2022-07-03"),
    (15, "Tom",       "Baker",     "tom.baker@baker.com",                "+44-161-999-0000", "UK",           "2022-08-05"),
    (16, "Aisha",     "Okonkwo",   "aisha.o@africa.net",                 "+234-80-1234-5678","Nigeria",      "2022-08-19"),
    (17, "Michael",   "Scott",     "michael.scott@dundermifflin.com",    "+1-570-555-0001",  "USA",          "2022-09-01"),
    (20, "Chris",     "Tanaka",    "chris.tanaka@japan.co.jp",           "+81-3-1234-5678",  "Japan",        "2022-10-18"),
    (23, "Grace",     "Osei",      "grace.osei@ghana.com",               "+233-24-123-4567", "Ghana",        "2022-12-01"),
    (24, "Lucas",     "Silva",     "lucas.silva@brazil.com.br",          "+55-11-9876-5432", "Brazil",       "2022-12-15"),
    (26, "Hannah",    "Mueller",   "hannah.m@deutschland.de",            "+49-89-1234-5678", "Germany",      "2023-01-18"),
    (29, "Elena",     "Vasquez",   "elena.v@spain.es",                   "+34-91-123-4567",  "Spain",        "2023-03-08"),

    # --- ISSUE: null email ---
    (18, "Mark",      "Davis",     None,                                 "+1-555-000-1234",  "USA",          "2022-09-14"),  # null email
    (27, "Yuki",      "Nakamura",  None,                                 "+61-2-9876-5432",  "Australia",    "2023-02-05"),  # null email
    (28, "Raj",       "Sharma",    None,                                 None,               "India",        "2023-02-20"),  # null email AND null phone

    # --- ISSUE: invalid email format ---
    (5,  "Charlie",   "McCarthy",  "charliemc@example",                  "+1-321-654-0987",  "USA",          "2022-03-12"),  # missing TLD
    (12, "Jennifer",  "Lee",       "jennifer.lee@noatsign",              "+1-614-555-0193",  "USA",          "2022-06-12"),  # no @ symbol
    (22, "Ben",       "Adams",     "ben@@adams.com",                     "+1-212-555-0100",  "USA",          "2022-11-20"),  # double @@

    # --- ISSUE: trailing space in first_name ---
    (8,  "Lisa ",     "Thompson",  "lisa.thompson@gmail.com",            "+1-503-555-0147",  "USA",          "2022-04-18"),  # trailing space
    (19, "Nina ",     "Petrov",    "nina.petrov@russia.ru",              "+7-495-123-4567",  "Russia",       "2022-10-02"),  # trailing space

    # --- ISSUE: invalid phone number ---
    (9,  "Robert",    "Brown",     "robert.brown@mail.com",              "ABCD-EFGH",        "Canada",       "2022-05-02"),  # letters in phone
    (14, "Fatima",    "Hassan",    "fatima.h@mail.com",                  "123",              "Nigeria",      "2022-07-20"),  # too short

    # --- ISSUE: null phone (nullable, for completeness_rate check) ---
    (21, "Sofia",     "Rossi",     "sofia.rossi@italy.it",               None,               "Italy",        "2022-11-05"),

    # --- ISSUE: duplicate email (same as customer 2) ---
    (25, "Oliver",    "Jones",     "sarah.chen@yahoo.com",               "+1-713-555-0156",  "USA",          "2023-01-03"),

    # --- ISSUE: first_name exceeds 50 characters ---
    (30, "Christopheralexanderbenjaminworthington", "III", "c.worthington@castle.co.uk", "+44-20-7946-1234", "UK", "2023-03-22"),
]

# ---------------------------------------------------------------------------
# Products — 20 rows
# Issues: 2 negative prices, 2 negative stock, 1 duplicate name,
#         1 null name, 2 orphan category_ids, 1 SKU exceeds max length
# ---------------------------------------------------------------------------
PRODUCTS = [
    # (product_id, product_name, category_id, price, stock_quantity, sku)
    # --- Valid records ---
    (1,  "Wireless Earbuds Pro",          1,  49.99,  150, "WEP-001"),
    (2,  "USB-C Hub 7-Port",              1,  34.99,  200, "UCH-002"),
    (4,  "Gaming Mouse",                  6,  59.99,  120, "GMO-004"),
    (6,  "Laptop Stand",                  2,  29.99,  300, "LPS-006"),
    (9,  "Bluetooth Speaker",             3,  79.99,  100, "BTS-009"),
    (10, "Webcam HD 1080p",               1,  45.99,   60, "WCM-010"),
    (13, "Screen Protector",              2,   8.99, 1000, "SPR-013"),
    (14, "Cable Organizer",               2,   9.99,  400, "COR-014"),
    (16, "Smart Home Hub",                4, 129.99,   45, "SHH-016"),
    (18, "Noise Cancelling Headphones",   3, 149.99,   70, "NCH-018"),
    (20, "Smart Doorbell",                4,  79.99,   55, "SDB-020"),

    # --- ISSUE: orphan category_id (categories 88 and 99 do not exist) ---
    (3,  "Mechanical Keyboard",          99,  89.99,   75, "MKB-003"),  # category 99 does not exist
    (11, "LED Desk Lamp",                88,  24.99,  250, "LDL-011"),  # category 88 does not exist

    # --- ISSUE: negative price ---
    (8,  "Smart Watch",                   5, -199.99,  80, "SWA-008"),  # negative price
    (15, "VR Headset",                    6, -299.99,  30, "VRH-015"),  # negative price

    # --- ISSUE: negative stock_quantity ---
    (12, "Portable Charger 20000mAh",     1,  39.99,  -25, "PCH-012"), # negative stock
    (19, "External SSD 1TB",              9,  89.99,  -10, "SSD-019"), # negative stock

    # --- ISSUE: duplicate product_name (same as product 1) ---
    (5,  "Wireless Earbuds Pro",          2,  44.99,   50, "WEP-005"), # duplicate name

    # --- ISSUE: null product_name ---
    (17, None,                            3,  19.99,  200, "NUL-017"), # null name

    # --- ISSUE: SKU exceeds 20 character max length ---
    (7,  "Phone Case",                    2,  12.99,  500, "THISISWAYTOOLONGSKU99"), # SKU > 20 chars
]

# ---------------------------------------------------------------------------
# Orders — 50 rows
# Issues: 3 negative totals, 1 null order_date, 2 invalid date formats,
#         4 null shipping_addresses, 2 orphan customer_ids, 2 invalid statuses
# ---------------------------------------------------------------------------
ORDERS = [
    # (order_id, customer_id, order_date, total_amount, shipping_address, status)
    # --- Valid records ---
    (1,  1,  "2023-01-05",  109.98, "42 Maple Ave, Austin TX 78701",          "delivered"),
    (2,  2,  "2023-01-07",   94.97, "88 Ocean Dr, San Francisco CA 94101",    "delivered"),
    (3,  4,  "2023-01-10",  125.98, "15 Baker St, London W1U 6SB",            "delivered"),
    (4,  6,  "2023-01-12",   29.99, None,                                     "delivered"),   # null shipping_address
    (5,  7,  "2023-01-15",  199.98, "33 Hangang-ro, Seoul 04798",             "delivered"),
    (6,  10, "2023-01-18",   89.99, "7 Marszalkowska, Warsaw 00-626",         "shipped"),
    (8,  11, "2023-01-25",  149.99, "12 Insurgentes Sur, Mexico City 03900",  "delivered"),
    (9,  13, "2023-01-28",   80.98, "22 Nanjing Rd, Shanghai 200001",         "delivered"),
    (10, 15, "2023-02-01",   79.99, "4 Coronation St, Manchester M1 4LH",     "delivered"),
    (11, 16, "2023-02-04",   59.99, "18 Broad St, Lagos 100001",              "processing"),
    (13, 17, "2023-02-10",  149.99, "1725 Slough Ave, Scranton PA 18503",     "delivered"),
    (14, 20, "2023-02-14",   94.98, "9-1 Ginza, Tokyo 104-0061",              "shipped"),
    (16, 23, "2023-02-21",  199.98, "31 Independence Ave, Accra 00233",       "delivered"),
    (17, 24, "2023-02-25",   79.99, "45 Paulista Ave, Sao Paulo 01310-100",   "delivered"),
    (18, 26, "2023-03-01",  149.99, "8 Leopoldstrasse, Munich 80802",         "processing"),
    (19, 29, "2023-03-05",   89.99, "2 Gran Via, Madrid 28013",               "shipped"),
    (20, 1,  "2023-03-08",   49.99, "42 Maple Ave, Austin TX 78701",          "delivered"),
    (21, 2,  "2023-03-10",   34.99, "88 Ocean Dr, San Francisco CA 94101",    "delivered"),
    (22, 4,  "2023-03-12",   59.99, "15 Baker St, London W1U 6SB",            "pending"),
    (24, 7,  "2023-03-18",  129.99, "33 Hangang-ro, Seoul 04798",             "delivered"),
    (25, 10, "2023-03-22",   39.99, "7 Marszalkowska, Warsaw 00-626",         "delivered"),
    (26, 11, "2023-03-25",   79.99, "12 Insurgentes Sur, Mexico City 03900",  "shipped"),
    (27, 13, "2023-03-28",  149.98, "22 Nanjing Rd, Shanghai 200001",         "delivered"),
    (28, 15, "2023-04-01",   18.98, "4 Coronation St, Manchester M1 4LH",     "delivered"),
    (29, 16, "2023-04-04",   59.99, None,                                     "pending"),    # null shipping_address
    (30, 17, "2023-04-08",   44.99, "45 Paulista Ave, Sao Paulo 01310-100",   "delivered"),
    (31, 24, "2023-04-12",   89.99, "45 Paulista Ave, Sao Paulo 01310-100",   "shipped"),
    (32, 26, "2023-04-15",  149.99, "8 Leopoldstrasse, Munich 80802",         "processing"),
    (33, 29, "2023-04-18",  129.99, "2 Gran Via, Madrid 28013",               "delivered"),
    (34, 1,  "2023-04-20",   49.99, "42 Maple Ave, Austin TX 78701",          "cancelled"),
    (35, 2,  "2023-04-22",   79.99, "88 Ocean Dr, San Francisco CA 94101",    "delivered"),
    (36, 4,  "2023-04-25",   24.99, "15 Baker St, London W1U 6SB",            "delivered"),
    (37, 7,  "2023-04-28",   59.99, "33 Hangang-ro, Seoul 04798",             "pending"),
    (38, 10, "2023-05-02",   89.99, None,                                     "shipped"),    # null shipping_address
    (39, 11, "2023-05-05",   49.99, "12 Insurgentes Sur, Mexico City 03900",  "delivered"),
    (40, 13, "2023-05-08",   34.99, "22 Nanjing Rd, Shanghai 200001",         "delivered"),
    (41, 15, "2023-05-10",   79.99, "4 Coronation St, Manchester M1 4LH",     "delivered"),
    (42, 16, "2023-05-14",   89.99, "18 Broad St, Lagos 100001",              "processing"),
    (43, 17, "2023-05-18",   59.99, "1725 Slough Ave, Scranton PA 18503",     "shipped"),
    (45, 24, "2023-05-24",  149.99, "45 Paulista Ave, Sao Paulo 01310-100",   "delivered"),
    (46, 26, "2023-05-28",   79.99, "8 Leopoldstrasse, Munich 80802",         "delivered"),
    (48, 29, "2023-06-03",   89.99, "2 Gran Via, Madrid 28013",               "pending"),
    (49, 1,  "2023-06-07",   49.99, "42 Maple Ave, Austin TX 78701",          "delivered"),

    # --- ISSUE: negative total_amount ---
    (7,  9,  "2023-01-20", -109.98, "55 Yonge St, Toronto ON M5E 1J4",        "cancelled"), # negative total
    (23, 6,  "2023-03-15",  -49.99, "Mumbai 400001",                          "cancelled"), # negative total
    (44, 21, "2023-05-21",  -29.99, "Via Roma 15, Milan 20121",               "cancelled"), # negative total

    # --- ISSUE: null order_date ---
    (50, 4,  None,           99.99, "15 Baker St, London W1U 6SB",            "pending"),   # null order_date

    # --- ISSUE: order_date with invalid format (not YYYY-MM-DD) ---
    (15, 20, "15/02/2023",   45.99, "9-1 Ginza, Tokyo 104-0061",              "delivered"), # DD/MM/YYYY format
    (47, 23, "March 5 2023", 79.99, "31 Independence Ave, Accra 00233",       "delivered"), # text format

    # --- ISSUE: null shipping_address (4th instance) ---
    (12, 10, "2023-02-08",   34.99, None,                                     "delivered"), # null shipping_address

    # --- ISSUE: orphan customer_id (customers 999 and 888 do not exist) ---
    (53, 999,"2023-06-10",   59.99, "Unknown Address",                        "pending"),   # orphan customer
    (54, 888,"2023-06-12",   89.99, "Unknown Address",                        "processing"),# orphan customer

    # --- ISSUE: invalid status value (not in allowed set) ---
    (55, 1,  "2023-06-15",   49.99, "42 Maple Ave, Austin TX 78701",          "DISPATCHED"),# invalid status
    (56, 2,  "2023-06-18",   34.99, "88 Ocean Dr, San Francisco CA 94101",    "on_hold"),   # invalid status
]

# ---------------------------------------------------------------------------
# Order Items — 75 rows
# Issues: 3 negative quantities, 2 negative unit_prices,
#         2 orphan order_ids, 2 orphan product_ids
# ---------------------------------------------------------------------------
ORDER_ITEMS = [
    # (item_id, order_id, product_id, quantity, unit_price)
    (1,  1,  1,  2,  49.99), (2,  1,  4,  1,  59.99),
    (3,  2,  2,  1,  34.99), (4,  2,  6,  2,  29.99),
    (5,  3,  9,  1,  79.99), (6,  3,  10, 1,  45.99),
    (7,  4,  6,  1,  29.99),
    (8,  5,  18, 1, 149.99), (9,  5,  1,  1,  49.99),
    (10, 6,  9,  1,  89.99),
    (11, 8,  18, 1, 149.99),
    (12, 9,  13, 3,   8.99), (13, 9,  14, 2,   9.99),
    (14, 10, 9,  1,  79.99),
    (15, 11, 4,  1,  59.99),
    (16, 13, 18, 1, 149.99),
    (17, 14, 1,  1,  49.99), (18, 14, 13, 5,   8.99),
    (19, 16, 18, 1, 149.99), (20, 16, 1,  1,  49.99),
    (21, 17, 9,  1,  79.99),
    (22, 18, 18, 1, 149.99),
    (23, 19, 9,  1,  89.99),
    (24, 20, 1,  1,  49.99),
    (25, 21, 2,  1,  34.99),
    (26, 22, 4,  1,  59.99),
    (27, 24, 16, 1, 129.99),
    (28, 25, 12, 1,  39.99),
    (29, 26, 9,  1,  79.99),
    (30, 27, 18, 1, 149.99), (31, 27, 13, 1,   8.99),
    (32, 28, 13, 1,   8.99), (33, 28, 14, 1,   9.99),
    (34, 29, 4,  1,  59.99),
    (35, 30, 5,  1,  44.99),
    (36, 31, 9,  1,  89.99),
    (37, 32, 18, 1, 149.99),
    (38, 33, 16, 1, 129.99),
    (39, 34, 1,  1,  49.99),
    (40, 35, 9,  1,  79.99),
    (41, 36, 11, 1,  24.99),
    (42, 37, 4,  1,  59.99),
    (43, 38, 9,  1,  89.99),
    (44, 39, 1,  1,  49.99),
    (45, 40, 2,  1,  34.99),
    (46, 41, 9,  1,  79.99),
    (47, 42, 9,  1,  89.99),
    (48, 43, 4,  1,  59.99),
    (49, 45, 18, 1, 149.99),
    (50, 46, 9,  1,  79.99),
    (51, 48, 9,  1,  89.99),
    (52, 49, 1,  1,  49.99),
    (53, 6,  10, 2,  45.99), (54, 6,  14, 3,   9.99),
    (55, 8,  6,  2,  29.99),
    (56, 11, 6,  2,  29.99),
    (57, 17, 6,  1,  29.99),
    (58, 19, 10, 1,  45.99),
    (59, 24, 4,  1,  59.99),
    (60, 33, 4,  1,  59.99),

    # --- ISSUE: negative quantity ---
    (61, 7,  1,  -2,  49.99),  # negative quantity
    (62, 23, 4,  -1,  59.99),  # negative quantity
    (63, 44, 9,  -3,  79.99),  # negative quantity

    # --- ISSUE: negative unit_price ---
    (64, 20, 8,  1, -199.99),  # negative unit_price (mirrors product issue)
    (65, 37, 15, 1, -299.99),  # negative unit_price

    # --- ISSUE: orphan order_id (orders 97, 98 do not exist) ---
    (66, 97, 1,  1,  49.99),   # orphan order_id
    (67, 98, 4,  1,  59.99),   # orphan order_id

    # --- ISSUE: orphan product_id (products 97, 98 do not exist) ---
    (68, 1,  97, 1,  29.99),   # orphan product_id
    (69, 2,  98, 2,  19.99),   # orphan product_id
]

# ---------------------------------------------------------------------------
# Payments — 40 rows
# Issues: 3 negative amounts, 3 invalid payment_method values,
#         2 invalid status values, 1 null payment_date
# ---------------------------------------------------------------------------
# Valid payment_method: credit_card, debit_card, paypal, bank_transfer, crypto
# Valid status:         completed, pending, failed, refunded
PAYMENTS = [
    # (payment_id, order_id, payment_date, amount, payment_method, status)
    (1,  1,  "2023-01-05",  109.98, "credit_card",   "completed"),
    (2,  2,  "2023-01-07",   94.97, "paypal",         "completed"),
    (3,  3,  "2023-01-10",  125.98, "debit_card",     "completed"),
    (4,  4,  "2023-01-12",   29.99, "credit_card",    "completed"),
    (5,  5,  "2023-01-15",  199.98, "bank_transfer",  "completed"),
    (6,  6,  "2023-01-18",   89.99, "credit_card",    "pending"),
    (7,  8,  "2023-01-25",  149.99, "paypal",         "completed"),
    (8,  9,  "2023-01-28",   80.98, "debit_card",     "completed"),
    (9,  10, "2023-02-01",   79.99, "credit_card",    "completed"),
    (10, 11, "2023-02-04",   59.99, "bank_transfer",  "pending"),
    (11, 13, "2023-02-10",  149.99, "credit_card",    "completed"),
    (12, 14, "2023-02-14",   94.98, "paypal",         "completed"),
    (13, 16, "2023-02-21",  199.98, "debit_card",     "completed"),
    (14, 17, "2023-02-25",   79.99, "credit_card",    "completed"),
    (15, 18, "2023-03-01",  149.99, "bank_transfer",  "pending"),
    (16, 19, "2023-03-05",   89.99, "credit_card",    "completed"),
    (17, 20, "2023-03-08",   49.99, "paypal",         "completed"),
    (18, 21, "2023-03-10",   34.99, "debit_card",     "completed"),
    (19, 22, "2023-03-12",   59.99, "credit_card",    "pending"),
    (20, 24, "2023-03-18",  129.99, "crypto",         "completed"),
    (21, 25, "2023-03-22",   39.99, "credit_card",    "completed"),
    (22, 26, "2023-03-25",   79.99, "paypal",         "completed"),
    (23, 27, "2023-03-28",  149.98, "bank_transfer",  "completed"),
    (24, 28, "2023-04-01",   18.98, "debit_card",     "completed"),
    (25, 29, "2023-04-04",   59.99, "credit_card",    "pending"),
    (26, 30, "2023-04-08",   44.99, "paypal",         "completed"),
    (27, 31, "2023-04-12",   89.99, "credit_card",    "completed"),
    (28, 32, "2023-04-15",  149.99, "bank_transfer",  "pending"),
    (29, 33, "2023-04-18",  129.99, "debit_card",     "completed"),
    (30, 34, "2023-04-20",   49.99, "credit_card",    "refunded"),

    # --- ISSUE: negative amount ---
    (31, 7,  "2023-01-20", -109.98, "credit_card",    "refunded"),  # negative amount
    (32, 23, "2023-03-15",  -49.99, "paypal",         "refunded"),  # negative amount
    (33, 44, "2023-05-21",  -29.99, "debit_card",     "refunded"),  # negative amount

    # --- ISSUE: invalid payment_method (not in allowed set) ---
    (34, 35, "2023-04-22",   79.99, "CASH",           "completed"), # invalid method
    (35, 36, "2023-04-25",   24.99, "check",          "completed"), # invalid method
    (36, 37, "2023-04-28",   59.99, "wire_transfer",  "completed"), # invalid method

    # --- ISSUE: invalid status (not in allowed set) ---
    (37, 38, "2023-05-02",   89.99, "credit_card",    "APPROVED"),  # invalid status
    (38, 39, "2023-05-05",   49.99, "paypal",         "processing"),# invalid status

    # --- ISSUE: null payment_date ---
    (39, 40, None,           34.99, "credit_card",    "pending"),   # null payment_date

    # --- valid ---
    (40, 41, "2023-05-10",   79.99, "bank_transfer",  "completed"),
]

# ---------------------------------------------------------------------------
# Reviews — 25 rows
# Issues: 3 ratings out of range (1-5), 2 orphan customer_ids,
#         2 orphan product_ids, 4 null review_text (nullable)
# ---------------------------------------------------------------------------
REVIEWS = [
    # (review_id, customer_id, product_id, rating, review_text, review_date)
    # --- Valid records ---
    (1,  1,  1,  5, "Excellent sound quality, very comfortable.",       "2023-02-10"),
    (2,  2,  2,  4, "Good hub, all ports work great.",                  "2023-02-15"),
    (3,  4,  9,  5, "Incredible bass, really impressed.",               "2023-02-20"),
    (4,  7,  18, 5, "Best headphones I have ever owned.",               "2023-02-25"),
    (5,  10, 6,  4, "Sturdy and stable, good quality.",                 "2023-03-01"),
    (6,  11, 9,  3, "Average sound, decent for the price.",             "2023-03-05"),
    (7,  13, 1,  5, "Perfect earbuds, great noise isolation.",          "2023-03-10"),
    (8,  15, 10, 4, "Clear picture, easy to set up.",                   "2023-03-15"),
    (9,  16, 4,  4, "Very responsive, comfortable grip.",               "2023-03-20"),
    (10, 17, 18, 5, "Outstanding noise cancellation.",                  "2023-03-25"),
    (11, 20, 2,  3, "Does the job but gets warm under load.",           "2023-04-01"),
    (12, 23, 16, 4, "Easy to configure, works with all my devices.",    "2023-04-05"),
    (13, 24, 9,  5, "Great portable speaker, loud and clear.",          "2023-04-10"),
    (14, 26, 18, 4, "Very effective noise cancellation.",               "2023-04-15"),
    (15, 29, 16, 5, "Seamlessly controls all my smart home devices.",   "2023-04-20"),

    # --- ISSUE: null review_text (nullable field) ---
    (16, 1,  4,  3, None, "2023-04-25"),  # null review_text
    (17, 2,  6,  4, None, "2023-04-28"),  # null review_text
    (18, 4,  13, 2, None, "2023-05-01"),  # null review_text
    (19, 7,  14, 5, None, "2023-05-04"),  # null review_text

    # --- ISSUE: rating out of valid range (must be 1-5) ---
    (20, 11, 1,  0, "Did not work at all.",                             "2023-05-08"),  # rating = 0
    (21, 13, 9,  6, "Too good, deserves more than 5 stars!",           "2023-05-12"),  # rating = 6
    (22, 15, 4, -1, "Terrible product.",                               "2023-05-15"),  # rating = -1

    # --- ISSUE: orphan customer_id (customers 501, 502 do not exist) ---
    (23, 501, 1, 4, "Pretty good earbuds overall.",                    "2023-05-18"),  # orphan customer
    (24, 502, 9, 5, "Best speaker in this price range.",               "2023-05-20"),  # orphan customer

    # --- ISSUE: orphan product_id (products 501, 502 do not exist) ---
    (25, 1,  501, 3, "It was okay.",                                   "2023-05-22"),  # orphan product
]


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------
def seed() -> None:
    db_path = Path(__file__).parent / "sample.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)

    conn.executemany("INSERT INTO category VALUES (?,?,?)", CATEGORIES)
    conn.executemany("INSERT INTO customer VALUES (?,?,?,?,?,?,?)", CUSTOMERS)
    conn.executemany("INSERT INTO product VALUES (?,?,?,?,?,?)", PRODUCTS)
    conn.executemany('INSERT INTO "order" VALUES (?,?,?,?,?,?)', ORDERS)
    conn.executemany("INSERT INTO order_item VALUES (?,?,?,?,?)", ORDER_ITEMS)
    conn.executemany("INSERT INTO payment VALUES (?,?,?,?,?,?)", PAYMENTS)
    conn.executemany("INSERT INTO review VALUES (?,?,?,?,?,?)", REVIEWS)

    conn.commit()
    conn.close()

    _print_summary(db_path)


def _print_summary(db_path: Path) -> None:
    print(f"\nDatabase seeded at: {db_path}")
    print(f"\n{'Table':<15} {'Rows':>6}   Intentional issues")
    print("-" * 72)
    rows = [
        ("category",    len(CATEGORIES),   "None — clean reference data"),
        ("customer",    len(CUSTOMERS),    "3 null emails, 3 invalid emails, 2 trailing spaces in name,\n" +
                                           " " * 25 + "1 duplicate email, 3 null phones, 2 invalid phones, 1 name > 50 chars"),
        ("product",     len(PRODUCTS),     "2 negative prices, 2 negative stock, 1 duplicate name,\n" +
                                           " " * 25 + "1 null name, 2 orphan category_ids, 1 SKU exceeds max length"),
        ("order",       len(ORDERS),       "3 negative totals, 1 null order_date, 2 invalid date formats,\n" +
                                           " " * 25 + "4 null shipping_addresses, 2 orphan customer_ids, 2 invalid statuses"),
        ("order_item",  len(ORDER_ITEMS),  "3 negative quantities, 2 negative unit_prices,\n" +
                                           " " * 25 + "2 orphan order_ids, 2 orphan product_ids"),
        ("payment",     len(PAYMENTS),     "3 negative amounts, 3 invalid payment_methods,\n" +
                                           " " * 25 + "2 invalid statuses, 1 null payment_date"),
        ("review",      len(REVIEWS),      "3 ratings out of range (1-5), 2 orphan customer_ids,\n" +
                                           " " * 25 + "1 orphan product_id, 4 null review_texts"),
    ]
    total_rows = 0
    for name, count, issues in rows:
        print(f"  {name:<13} {count:>6}   {issues}")
        total_rows += count
    print("-" * 72)
    print(f"  {'TOTAL':<13} {total_rows:>6}\n")


if __name__ == "__main__":
    seed()
