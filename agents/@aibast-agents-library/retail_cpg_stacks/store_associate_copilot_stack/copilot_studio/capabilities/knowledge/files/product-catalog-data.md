# Store Product Catalog

> SYNTHETIC — DEMO DATA. Every SKU, brand, price, location, and stock count in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real item master, planogram, and inventory system (see the README's
> production section).

The catalog holds exactly 10 products, SKU-1001 through SKU-1010. Nothing
outside this list exists.

## Core attributes

| SKU | Name | Category | Brand | Price | Aisle | Shelf | On Hand | UPC |
|-----|------|----------|-------|-------|-------|-------|---------|-----|
| SKU-1001 | Classic Denim Jacket | Apparel | Heritage Line | $89.99 | A3 | Top rack | 74 | 0-12345-67890-1 |
| SKU-1002 | Wireless Earbuds Pro | Electronics | SoundWave | $59.99 | E1 | Locked case | 132 | 0-12345-67890-2 |
| SKU-1003 | Organic Cotton T-Shirt | Apparel | EcoBasics | $29.99 | A1 | Mid rack | 210 | 0-12345-67890-3 |
| SKU-1004 | Smart Fitness Tracker | Electronics | FitPulse | $129.99 | E2 | Display stand | 45 | 0-12345-67890-4 |
| SKU-1005 | Premium Running Shoes | Footwear | StrideMax | $149.99 | F1 | Wall display | 38 | 0-12345-67890-5 |
| SKU-1006 | Stainless Water Bottle | Accessories | HydroKeep | $24.99 | C2 | End cap | 195 | 0-12345-67890-6 |
| SKU-1007 | Leather Crossbody Bag | Accessories | UrbanCraft | $79.99 | B2 | Display hooks | 61 | 0-12345-67890-7 |
| SKU-1008 | UV Protection Sunglasses | Accessories | ClearView | $44.99 | B1 | Rotating display | 88 | 0-12345-67890-8 |
| SKU-1009 | Performance Yoga Mat | Fitness | ZenGrip | $54.99 | F2 | Standing rack | 42 | 0-12345-67890-9 |
| SKU-1010 | Aromatherapy Candle Set | Home | Luminary | $34.99 | D1 | Feature table | 67 | 0-12345-67891-0 |

Categories in use: Apparel (2), Electronics (2), Accessories (3), Footwear (1),
Fitness (1), Home (1).

## Sizes, colors, materials, and care

| SKU | Sizes | Colors | Materials | Care |
|-----|-------|--------|-----------|------|
| SKU-1001 | XS, S, M, L, XL, XXL | Indigo Wash, Light Blue, Black | 100% cotton denim, brass buttons | Machine wash cold, tumble dry low |
| SKU-1002 | One Size | Matte Black, Pearl White, Navy | ABS plastic, silicone ear tips | Wipe with dry cloth. Do not submerge. |
| SKU-1003 | XS, S, M, L, XL | White, Heather Grey, Black, Sage Green, Dusty Rose | 100% GOTS-certified organic cotton | Machine wash cold with like colors |
| SKU-1004 | S/M Band, L/XL Band | Midnight Black, Arctic White, Forest Green | Aluminum case, fluoroelastomer band | Rinse with fresh water after swimming |
| SKU-1005 | 7, 7.5, 8, 8.5, 9, 9.5, 10, 10.5, 11, 12, 13 | Cloud White/Grey, Black/Volt, Navy/Orange | Engineered mesh upper, EVA foam midsole, rubber outsole | Spot clean with damp cloth. Air dry only. |
| SKU-1006 | 20oz, 32oz | Brushed Steel, Matte Black, Ocean Blue, Coral | 18/8 stainless steel, BPA-free lid | Hand wash recommended. Dishwasher safe (top rack). |
| SKU-1007 | One Size | Cognac, Black, Olive | Full-grain leather, brass hardware | Condition with leather balm quarterly |
| SKU-1008 | Standard, Wide | Tortoise, Matte Black, Crystal Clear | Acetate frame, polarized CR-39 lenses | Clean with included microfiber cloth. Store in case. |
| SKU-1009 | 68x24 in, 72x26 in | Midnight Purple, Sage, Charcoal | Natural rubber base, polyurethane top layer | Wipe with damp cloth after use. Air dry flat. |
| SKU-1010 | 3-pack (4oz each) | Lavender/Eucalyptus/Vanilla | Soy wax, cotton wicks, essential oils | Trim wick to 1/4 inch before lighting. Burn max 4 hours. |

The size and color lists say what the product comes in — not what is on the
shelf right now. `On Hand` is a single store-level count with no size or color
breakdown.

## Key features

| SKU | Key Features |
|-----|--------------|
| SKU-1001 | Adjustable waist tabs; Two chest pockets; Vintage fade finish |
| SKU-1002 | Active noise cancellation; 8-hour battery; IPX4 water resistant; Bluetooth 5.3 |
| SKU-1003 | Pre-shrunk; Tagless comfort label; Reinforced shoulder seams |
| SKU-1004 | Heart rate monitor; GPS tracking; Sleep analysis; 7-day battery; 5ATM water resistant |
| SKU-1005 | Responsive cushioning; Breathable knit upper; Reflective accents; Carbon fiber plate |
| SKU-1006 | Double-wall vacuum insulation; 24h cold / 12h hot; Leak-proof lid; Wide mouth |
| SKU-1007 | Adjustable strap; RFID-blocking pocket; Three compartments; YKK zippers |
| SKU-1008 | 100% UV400 protection; Polarized lenses; Spring hinges; Scratch-resistant coating |
| SKU-1009 | Non-slip grip; 6mm thickness; Alignment lines; Carrying strap included |
| SKU-1010 | Clean-burning soy wax; 40-hour burn time per candle; Reusable glass jars; No synthetic fragrances |

## Complementary products

Every SKU has exactly two suggested pairings. These are the only pairings the
agent may suggest, and they drive the `{complementary_product}` slot in the
upsell script.

| SKU | Product | Pairs Well With |
|-----|---------|-----------------|
| SKU-1001 | Classic Denim Jacket | Organic Cotton T-Shirt (SKU-1003), UV Protection Sunglasses (SKU-1008) |
| SKU-1002 | Wireless Earbuds Pro | Smart Fitness Tracker (SKU-1004), Stainless Water Bottle (SKU-1006) |
| SKU-1003 | Organic Cotton T-Shirt | Classic Denim Jacket (SKU-1001), UV Protection Sunglasses (SKU-1008) |
| SKU-1004 | Smart Fitness Tracker | Premium Running Shoes (SKU-1005), Performance Yoga Mat (SKU-1009) |
| SKU-1005 | Premium Running Shoes | Stainless Water Bottle (SKU-1006), Performance Yoga Mat (SKU-1009) |
| SKU-1006 | Stainless Water Bottle | Performance Yoga Mat (SKU-1009), Premium Running Shoes (SKU-1005) |
| SKU-1007 | Leather Crossbody Bag | UV Protection Sunglasses (SKU-1008), Classic Denim Jacket (SKU-1001) |
| SKU-1008 | UV Protection Sunglasses | Leather Crossbody Bag (SKU-1007), Classic Denim Jacket (SKU-1001) |
| SKU-1009 | Performance Yoga Mat | Stainless Water Bottle (SKU-1006), Smart Fitness Tracker (SKU-1004) |
| SKU-1010 | Aromatherapy Candle Set | Performance Yoga Mat (SKU-1009), Stainless Water Bottle (SKU-1006) |
