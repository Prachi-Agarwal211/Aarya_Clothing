"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Search, Filter, ChevronDown, ChevronLeft, ChevronRight } from "lucide-react";
import Header from "../../../components/Header";
import ProductCard from "../../../components/ProductCard";
import ProductModal from "../../../components/ProductModal";
import { categoryData, getCategoryTitle, getCategoryDescription, Product } from "../../data/categories";

// Next.js 15+ compatible props for dynamic routes
export default function CategoryPage({ params }: { params: Promise<{ slug: string }> }) {
    const [slug, setSlug] = useState<string>("");
    const [products, setProducts] = useState<Product[]>([]);
    const [filteredProducts, setFilteredProducts] = useState<Product[]>([]);
    const [searchTerm, setSearchTerm] = useState("");
    const [sortBy, setSortBy] = useState("featured");
    const [selectedSizes, setSelectedSizes] = useState<string[]>([]);

    // Modal State
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

    // Pagination state
    const [currentPage, setCurrentPage] = useState(1);
    const ITEMS_PER_PAGE = 20;

    // Mobile filter state
    const [showFilters, setShowFilters] = useState(false);

    const sizes = ["XS", "S", "M", "L", "XL", "XXL"];

    useEffect(() => {
        const unwrapParams = async () => {
            const resolvedParams = await params;
            setSlug(resolvedParams.slug);

            const categoryProducts = categoryData[resolvedParams.slug] || [];
            setProducts(categoryProducts);
            setFilteredProducts(categoryProducts);
        };

        unwrapParams();
    }, [params]);

    useEffect(() => {
        let filtered = products.filter(product => {
            const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase());
            return matchesSearch;
        });

        if (sortBy === "price-low") filtered.sort((a, b) => a.price - b.price);
        else if (sortBy === "price-high") filtered.sort((a, b) => b.price - a.price);
        else if (sortBy === "name") filtered.sort((a, b) => a.name.localeCompare(b.name));

        setFilteredProducts(filtered);
        setCurrentPage(1);
    }, [products, searchTerm, sortBy]);

    const toggleSize = (size: string) => {
        setSelectedSizes(prev => prev.includes(size) ? prev.filter(s => s !== size) : [...prev, size]);
    };

    const handleProductClick = (product: Product) => {
        setSelectedProduct(product);
    };

    // Pagination Logic
    const totalPages = Math.ceil(filteredProducts.length / ITEMS_PER_PAGE);
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const paginatedProducts = filteredProducts.slice(startIndex, startIndex + ITEMS_PER_PAGE);

    const handlePageChange = (page: number) => {
        if (page >= 1 && page <= totalPages) {
            setCurrentPage(page);
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
    };

    if (!slug) return <div className="min-h-screen bg-[#0B0B0C] flex items-center justify-center text-[#EAEAEA]">Loading...</div>;

    return (
        <div className="min-h-screen bg-[#0B0B0C]">
            <Header />

            {/* Spacer for fixed header */}
            <div className="h-24"></div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

                {/* Page Title */}
                <div className="mb-8 text-center md:text-left">
                    <h1 className="text-3xl md:text-4xl font-serif text-[#C9A227] mb-2">{getCategoryTitle(slug)}</h1>
                    <p className="text-[#9CA3AF]">{getCategoryDescription(slug)}</p>
                </div>

                {/* Top Filter Bar */}
                <div className="mb-10 sticky top-20 z-40 bg-[#0B0B0C]/90 backdrop-blur-md py-4 border-b border-[#262626]">
                    <div className="flex flex-col md:flex-row gap-4 items-center justify-between">

                        {/* Search */}
                        <div className="relative w-full md:w-64">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[#9CA3AF] w-4 h-4" />
                            <input
                                type="text"
                                placeholder="Search products..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 bg-[#151517] border border-[#262626] rounded-full text-[#EAEAEA] placeholder-[#9CA3AF] focus:outline-none focus:border-[#C9A227] transition-colors"
                            />
                        </div>

                        {/* Quick Filters (Chips) - Desktop */}
                        <div className="hidden md:flex flex-wrap gap-2 items-center flex-1 justify-center">
                            {sizes.slice(0, 4).map((size) => (
                                <button
                                    key={size}
                                    onClick={() => toggleSize(size)}
                                    className={`px-4 py-1.5 rounded-full text-sm transition-all border ${selectedSizes.includes(size)
                                            ? "bg-[#C9A227] text-black border-[#C9A227]"
                                            : "bg-[#151517] text-[#EAEAEA] border-[#262626] hover:border-[#C9A227]"
                                        }`}
                                >
                                    {size}
                                </button>
                            ))}
                        </div>

                        {/* Sort & Mobile Filter Toggle */}
                        <div className="flex items-center gap-3 w-full md:w-auto">
                            <div className="relative flex-1 md:flex-none">
                                <select
                                    value={sortBy}
                                    onChange={(e) => setSortBy(e.target.value)}
                                    className="w-full md:w-48 appearance-none px-4 py-2 bg-[#151517] border border-[#262626] rounded-full text-[#EAEAEA] focus:outline-none focus:border-[#C9A227] cursor-pointer"
                                >
                                    <option value="featured">Featured</option>
                                    <option value="price-low">Price: Low to High</option>
                                    <option value="price-high">Price: High to Low</option>
                                </select>
                                <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 text-[#9CA3AF] w-4 h-4 pointer-events-none" />
                            </div>

                            <button
                                className="md:hidden p-2 bg-[#151517] text-[#EAEAEA] border border-[#262626] rounded-full"
                                onClick={() => setShowFilters(!showFilters)}
                            >
                                <Filter className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Mobile Extended Filters */}
                    {showFilters && (
                        <div className="md:hidden mt-4 p-4 bg-[#151517] rounded-xl border border-[#262626] animate-fade-in-up">
                            <div className="mb-4">
                                <h4 className="text-[#EAEAEA] font-medium mb-2">Sizes</h4>
                                <div className="flex flex-wrap gap-2">
                                    {sizes.map((size) => (
                                        <button
                                            key={size}
                                            onClick={() => toggleSize(size)}
                                            className={`px-3 py-1 rounded-full text-xs border ${selectedSizes.includes(size)
                                                    ? "bg-[#C9A227] text-black border-[#C9A227]"
                                                    : "bg-[#0B0B0C] text-[#EAEAEA] border-[#262626]"
                                                }`}
                                        >
                                            {size}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Product Grid */}
                {products.length > 0 ? (
                    filteredProducts.length > 0 ? (
                        <>
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 md:gap-8">
                                {paginatedProducts.map((product) => (
                                    <div key={product.id} onClick={() => handleProductClick(product)} className="cursor-pointer">
                                        <ProductCard
                                            id={product.id}
                                            name={product.name}
                                            price={product.price}
                                            image={product.image}
                                            category={product.category}
                                        />
                                    </div>
                                ))}
                            </div>

                            {/* Pagination Controls */}
                            {totalPages > 1 && (
                                <div className="mt-12 flex justify-center items-center gap-4">
                                    <button
                                        onClick={() => handlePageChange(currentPage - 1)}
                                        disabled={currentPage === 1}
                                        className="p-2 rounded-full border border-[#262626] text-[#EAEAEA] hover:border-[#C9A227] hover:text-[#C9A227] disabled:opacity-50 disabled:hover:border-[#262626] disabled:hover:text-[#EAEAEA] transition-colors"
                                    >
                                        <ChevronLeft className="w-5 h-5" />
                                    </button>

                                    <div className="flex items-center gap-2">
                                        {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                                            <button
                                                key={page}
                                                onClick={() => handlePageChange(page)}
                                                className={`w-8 h-8 rounded-full text-sm font-medium transition-colors ${currentPage === page
                                                        ? "bg-[#C9A227] text-black"
                                                        : "text-[#EAEAEA] hover:bg-[#151517] hover:text-[#C9A227]"
                                                    }`}
                                            >
                                                {page}
                                            </button>
                                        ))}
                                    </div>

                                    <button
                                        onClick={() => handlePageChange(currentPage + 1)}
                                        disabled={currentPage === totalPages}
                                        className="p-2 rounded-full border border-[#262626] text-[#EAEAEA] hover:border-[#C9A227] hover:text-[#C9A227] disabled:opacity-50 disabled:hover:border-[#262626] disabled:hover:text-[#EAEAEA] transition-colors"
                                    >
                                        <ChevronRight className="w-5 h-5" />
                                    </button>
                                </div>
                            )}

                            <p className="text-center text-[#9CA3AF] text-sm mt-6">
                                Showing {startIndex + 1}-{Math.min(startIndex + ITEMS_PER_PAGE, filteredProducts.length)} of {filteredProducts.length} products
                            </p>
                        </>
                    ) : (
                        <div className="text-center py-20">
                            <p className="text-[#9CA3AF] text-lg">No products found matching your criteria.</p>
                            <button
                                onClick={() => { setSearchTerm(""); setSortBy("featured"); setSelectedSizes([]); }}
                                className="mt-6 px-6 py-2 bg-[#C9A227] text-black rounded-full hover:bg-white transition-colors"
                            >
                                Clear Filters
                            </button>
                        </div>
                    )
                ) : (
                    <div className="text-center py-20">
                        <p className="text-[#9CA3AF] text-lg">No products found in this category yet.</p>
                        <Link href="/" className="mt-6 inline-block px-6 py-2 bg-[#C9A227] text-black rounded-full hover:bg-white transition-colors">
                            Back to Home
                        </Link>
                    </div>
                )}
            </div>

            {/* Product Modal */}
            {selectedProduct && selectedProduct.id && (
                <ProductModal product={selectedProduct} onClose={() => setSelectedProduct(null)} />
            )}
        </div>
    );
}
