INSERT INTO customers (name, email, password) VALUES
('Alice Gonzaga', 'alice@email.com', 'hashedpassword1'),
('Bob Hermez', 'bob@email.com', 'hashedpassword2');

INSERT INTO restaurants (name, address) VALUES
('Pizza Place', '123 Main St'),
('Sushi World', '456 Ocean Ave');

INSERT INTO menu_items (restaurant_id, name, price) VALUES
(1, 'Cheese', 10.00),
(1, 'Pepperoni', 12.00),
(2, 'Spicy Tuna Roll', 15.00);

INSERT INTO orders (customer_id, restaurant_id, total, status) VALUES
(1, 2, 25.00, 'delivered'),
(1, 1, 15.00, 'pending');

INSERT INTO order_items (order_id, item_id, quantity) VALUES
(1, 3, 1),
(2, 1, 2);
