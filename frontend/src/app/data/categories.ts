export interface Product {
    id: number;
    name: string;
    price: number;
    image: string; // Keep for backward compatibility/thumbnail
    images?: string[]; // For slider
    category: string;
    description?: string;
    sizes?: string[];
    color?: string;
}

const defaultDescription = "Experience luxury with this exquisitely crafted outfit. Made from premium fabrics, it offers both comfort and style, perfect for weddings, parties, or festive occasions. The intricate detailing and modern cut make it a must-have for your wardrobe.";
const defaultSizes = ["XS", "S", "M", "L", "XL", "XXL"];

// Helper to enhance sample data
const enhance = (product: any): Product => ({
    ...product,
    description: defaultDescription,
    sizes: defaultSizes,
    // Use the main image as the first slider image, plus some placeholders
    images: [product.image, "/placeholder-new.jpg", "/placeholder-women.jpg", "/placeholder-ethnic.jpg"],
    color: "Multicolor"
});

const rawData: Record<string, any[]> = {
    "kurti-set": [
        { id: 1, name: "Elegant Embroidered Kurti Set", price: 2999, image: "/placeholder-women.jpg", category: "Kurti Set" },
        { id: 2, name: "Traditional Anarkali Set", price: 3499, image: "/placeholder-new.jpg", category: "Kurti Set" },
        { id: 3, name: "Designer Palazzo Set", price: 2799, image: "/placeholder-men.jpg", category: "Kurti Set" },
        { id: 4, name: "Festive Wear Kurti Set", price: 4299, image: "/placeholder-ethnic.jpg", category: "Kurti Set" },
        { id: 5, name: "Casual Cotton Kurti Set", price: 1999, image: "/placeholder-western.jpg", category: "Kurti Set" },
        { id: 6, name: "Party Wear Designer Set", price: 5299, image: "/placeholder-wedding.jpg", category: "Kurti Set" },
        { id: 7, name: "Silk Blend Kurti Set", price: 3899, image: "/placeholder-women.jpg", category: "Kurti Set" },
        { id: 8, name: "Printed Summer Set", price: 2299, image: "/placeholder-new.jpg", category: "Kurti Set" },
        { id: 9, name: "Heavy Work Bridal Set", price: 8999, image: "/placeholder-men.jpg", category: "Kurti Set" },
        { id: 10, name: "Minimalist Office Set", price: 2499, image: "/placeholder-ethnic.jpg", category: "Kurti Set" },
        { id: 11, name: "Floral Print Kurti Set", price: 2699, image: "/placeholder-western.jpg", category: "Kurti Set" },
        { id: 12, name: "Royal Blue Designer Set", price: 4599, image: "/placeholder-wedding.jpg", category: "Kurti Set" },
        { id: 13, name: "Velvet Party Wear Set", price: 5999, image: "/placeholder-women.jpg", category: "Kurti Set" },
        { id: 14, name: "Georgette Mirror Work Set", price: 4799, image: "/placeholder-new.jpg", category: "Kurti Set" },
        { id: 15, name: "Lucknowi Chikankari Set", price: 3299, image: "/placeholder-men.jpg", category: "Kurti Set" },
        { id: 16, name: "Banarasi Silk Kurti Set", price: 6499, image: "/placeholder-ethnic.jpg", category: "Kurti Set" },
        { id: 17, name: "Pastel Green Sharara Set", price: 3599, image: "/placeholder-western.jpg", category: "Kurti Set" },
        { id: 18, name: "Maroon Velvet Suit", price: 5499, image: "/placeholder-wedding.jpg", category: "Kurti Set" },
        { id: 19, name: "Yellow Haldi Special Set", price: 2199, image: "/placeholder-women.jpg", category: "Kurti Set" },
        { id: 20, name: "Black Sequin Kurti Set", price: 3999, image: "/placeholder-new.jpg", category: "Kurti Set" },
        { id: 21, name: "Teal Blue Anarkali", price: 4199, image: "/placeholder-men.jpg", category: "Kurti Set" },
        { id: 22, name: "Peach Cotton Daily Wear", price: 1899, image: "/placeholder-ethnic.jpg", category: "Kurti Set" },
        { id: 23, name: "Orange Festive Set", price: 3399, image: "/placeholder-western.jpg", category: "Kurti Set" },
        { id: 24, name: "Grey Embroidered Suit", price: 2899, image: "/placeholder-wedding.jpg", category: "Kurti Set" },
    ],
    "cord-sets": [
        { id: 101, name: "Floral Co-ord Set", price: 1899, image: "/placeholder-women.jpg", category: "Cord Set" },
        { id: 102, name: "Abstract Print Set", price: 2199, image: "/placeholder-new.jpg", category: "Cord Set" },
        { id: 103, name: "Linen Summer Set", price: 2499, image: "/placeholder-men.jpg", category: "Cord Set" },
        { id: 104, name: "Formal Blazer Set", price: 3999, image: "/placeholder-ethnic.jpg", category: "Cord Set" },
        { id: 105, name: "Satin Night Set", price: 1599, image: "/placeholder-western.jpg", category: "Cord Set" },
        { id: 106, name: "Boho Chic Co-ord", price: 2799, image: "/placeholder-wedding.jpg", category: "Cord Set" },
        { id: 107, name: "Striped Cotton Set", price: 1999, image: "/placeholder-women.jpg", category: "Cord Set" },
        { id: 108, name: "Velvet Winter Set", price: 4599, image: "/placeholder-new.jpg", category: "Cord Set" },
    ],
    "gowns": [
        { id: 201, name: "Royal Blue Evening Gown", price: 8999, image: "/placeholder-wedding.jpg", category: "Gown" },
        { id: 202, name: "Emerald Green Satin Gown", price: 7499, image: "/placeholder-women.jpg", category: "Gown" },
        { id: 203, name: "Red Carpet Designer Gown", price: 12999, image: "/placeholder-new.jpg", category: "Gown" },
        { id: 204, name: "Floral Chiffon Gown", price: 4999, image: "/placeholder-ethnic.jpg", category: "Gown" },
        { id: 205, name: "Black Sequin Party Gown", price: 9999, image: "/placeholder-men.jpg", category: "Gown" },
        { id: 206, name: "Pastel Pink Prom Gown", price: 6599, image: "/placeholder-western.jpg", category: "Gown" },
        { id: 207, name: "Gold Embroidered Ball Gown", price: 15999, image: "/placeholder-wedding.jpg", category: "Gown" },
        { id: 208, name: "Silver Mermaid Cut Gown", price: 11499, image: "/placeholder-women.jpg", category: "Gown" },
        { id: 209, name: "Burgundy Velvet Gown", price: 8499, image: "/placeholder-new.jpg", category: "Gown" },
        { id: 210, name: "Peach Tulle Princess Gown", price: 7999, image: "/placeholder-ethnic.jpg", category: "Gown" },
        { id: 211, name: "Navy Blue Silk Gown", price: 9299, image: "/placeholder-men.jpg", category: "Gown" },
        { id: 212, name: "Off-White Lace Gown", price: 6999, image: "/placeholder-western.jpg", category: "Gown" },
        { id: 213, name: "Lavender Off-Shoulder Gown", price: 5499, image: "/placeholder-women.jpg", category: "Gown" },
        { id: 214, name: "Maroon Georgette Gown", price: 4999, image: "/placeholder-new.jpg", category: "Gown" },
        { id: 215, name: "Teal Anarkali Gown", price: 6499, image: "/placeholder-ethnic.jpg", category: "Gown" },
        { id: 216, name: "Rose Gold Sequin Gown", price: 13999, image: "/placeholder-wedding.jpg", category: "Gown" },
        { id: 217, name: "Black Slit Gown", price: 7999, image: "/placeholder-men.jpg", category: "Gown" },
        { id: 218, name: "Yellow Haldi Gown", price: 4499, image: "/placeholder-western.jpg", category: "Gown" },
        { id: 219, name: "Grey Net Gown", price: 5999, image: "/placeholder-women.jpg", category: "Gown" },
        { id: 220, name: "Orange Ruffle Gown", price: 7499, image: "/placeholder-new.jpg", category: "Gown" },
        { id: 221, name: "Printed Boho Gown", price: 3999, image: "/placeholder-ethnic.jpg", category: "Gown" },
        { id: 222, name: "White Bridal Gown", price: 24999, image: "/placeholder-wedding.jpg", category: "Gown" },
    ],
    "sarees": [
        { id: 301, name: "Banarasi Silk Saree", price: 15999, image: "/placeholder-ethnic.jpg", category: "Saree" },
        { id: 302, name: "Kanjivaram Gold Saree", price: 18999, image: "/placeholder-wedding.jpg", category: "Saree" },
        { id: 303, name: "Chiffon Floral Saree", price: 2499, image: "/placeholder-women.jpg", category: "Saree" },
        { id: 304, name: "Georgette Party Wear", price: 3999, image: "/placeholder-new.jpg", category: "Saree" },
        { id: 305, name: "Cotton Handloom Saree", price: 1999, image: "/placeholder-men.jpg", category: "Saree" },
        { id: 306, name: "Designer Net Saree", price: 5999, image: "/placeholder-western.jpg", category: "Saree" },
    ],
    "kurtis": [
        { id: 401, name: "Daily Wear Cotton Kurti", price: 999, image: "/placeholder-western.jpg", category: "Kurti" },
        { id: 402, name: "Printed Rayon Kurti", price: 1299, image: "/placeholder-women.jpg", category: "Kurti" },
        { id: 403, name: "Embroidered Festive Kurti", price: 2499, image: "/placeholder-ethnic.jpg", category: "Kurti" },
        { id: 404, name: "A-Line Designer Kurti", price: 1899, image: "/placeholder-new.jpg", category: "Kurti" },
        { id: 405, name: "Short Tunic Kurti", price: 899, image: "/placeholder-men.jpg", category: "Kurti" },
    ],
    "duppatas": [
        { id: 501, name: "Phulkari Heavy Duppata", price: 2999, image: "/placeholder-ethnic.jpg", category: "Duppata" },
        { id: 502, name: "Silk Banarasi Duppata", price: 3499, image: "/placeholder-wedding.jpg", category: "Duppata" },
        { id: 503, name: "Net Embroidered Duppata", price: 1599, image: "/placeholder-women.jpg", category: "Duppata" },
        { id: 504, name: "Cotton Printed Duppata", price: 899, image: "/placeholder-new.jpg", category: "Duppata" },
    ]
};

// Export the enhanced data
export const categoryData: Record<string, Product[]> = {};

for (const key in rawData) {
    categoryData[key] = rawData[key].map(enhance);
}

export const getCategoryTitle = (slug: string) => {
    const titles: Record<string, string> = {
        "kurti-set": "Kurti Set Collection",
        "cord-sets": "Cord Sets & Co-ords",
        "gowns": "Designer Gowns",
        "sarees": "Exquisite Sarees",
        "kurtis": "Kurtis & Tunics",
        "duppatas": "Premium Duppatas"
    };
    return titles[slug] || "Collection";
};

export const getCategoryDescription = (slug: string) => {
    const descriptions: Record<string, string> = {
        "kurti-set": "Discover our premium range of ethnic wear",
        "cord-sets": "Trendy and comfortable co-ord sets for every occasion",
        "gowns": "Elegance woven into every thread for your special nights",
        "sarees": "Traditional grace meets modern sophistication",
        "kurtis": "Chic and versatile kurtis for daily and festive wear",
        "duppatas": "Add a touch of royalty to your outfit"
    };
    return descriptions[slug] || "Explore our latest collection";
};
