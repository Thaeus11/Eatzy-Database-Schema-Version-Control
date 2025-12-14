ALTER TABLE customers ADD COLUMN phone VARCHAR(20);
ALTER TABLE menu_items ADD COLUMN description TEXT;
ALTER TABLE restaurants MODIFY address VARCHAR(255);
ALTER TABLE menu_items ADD CONSTRAINT unique_menu_name_per_restaurant UNIQUE (restaurant_id, name);
