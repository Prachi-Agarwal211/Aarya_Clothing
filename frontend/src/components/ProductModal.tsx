"use client";

import { useState } from "react";
import Image from "next/image";
import { X, ChevronLeft, ChevronRight, ShoppingBag, Heart, Minus, Plus } from "lucide-react";
import { Product } from "../app/data/categories";

interface ProductModalProps {
    product: Product;
    onClose: () => void;
}

export default function ProductModal({ product, onClose }: ProductModalProps) {
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const [selectedSize, setSelectedSize] = useState("");
    const [quantity, setQuantity] = useState(1);

    const images = product.images && product.images.length > 0 ? product.images : [product.image];

    const nextImage = () => {
        setCurrentImageIndex((prev) => (prev + 1) % images.length);
    };

    const prevImage = () => {
        setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/80 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            ></div>

            {/* Modal Content */}
            <div className="relative bg-[#151517] w-full max-w-5xl rounded-3xl overflow-hidden shadow-2xl flex flex-col md:flex-row h-[90vh] md:h-auto animate-fade-in-up border border-[#262626]">

                {/* Close Button (Mobile) */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 z-50 p-2 bg-black/50 text-white rounded-full md:hidden"
                >
                    <X className="w-6 h-6" />
                </button>

                {/* Left: Image Slider */}
                <div className="w-full md:w-1/2 h-[40vh] md:h-[600px] relative bg-[#0B0B0C]">
                    <Image
                        src={images[currentImageIndex]}
                        alt={product.name}
                        fill
                        className="object-cover"
                    />

                    {/* Slider Controls */}
                    {images.length > 1 && (
                        <>
                            <button
                                onClick={prevImage}
                                className="absolute left-4 top-1/2 transform -translate-y-1/2 p-2 bg-black/50 text-white rounded-full hover:bg-[#C9A227] transition-colors"
                            >
                                <ChevronLeft className="w-6 h-6" />
                            </button>
                            <button
                                onClick={nextImage}
                                className="absolute right-4 top-1/2 transform -translate-y-1/2 p-2 bg-black/50 text-white rounded-full hover:bg-[#C9A227] transition-colors"
                            >
                                <ChevronRight className="w-6 h-6" />
                            </button>

                            {/* Dots */}
                            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2">
                                {images.map((_, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => setCurrentImageIndex(idx)}
                                        className={`w-2 h-2 rounded-full transition-all ${currentImageIndex === idx ? "bg-[#C9A227] w-4" : "bg-white/50"
                                            }`}
                                    />
                                ))}
                            </div>
                        </>
                    )}
                </div>

                {/* Right: Details */}
                <div className="w-full md:w-1/2 p-6 md:p-10 overflow-y-auto custom-scrollbar bg-[#151517]">
                    {/* Close Button (Desktop) */}
                    <button
                        onClick={onClose}
                        className="absolute top-6 right-6 text-[#9CA3AF] hover:text-[#EAEAEA] hidden md:block"
                    >
                        <X className="w-6 h-6" />
                    </button>

                    <div className="mb-2">
                        <span className="text-[#C9A227] text-sm tracking-widest uppercase font-medium">{product.category}</span>
                    </div>

                    <h2 className="text-3xl font-serif text-[#EAEAEA] mb-4">{product.name}</h2>

                    <div className="flex items-center gap-4 mb-6">
                        <span className="text-2xl font-semibold text-[#EAEAEA]">₹{product.price.toLocaleString('en-IN')}</span>
                        <span className="text-[#9CA3AF] text-sm">(Inclusive of all taxes)</span>
                    </div>

                    <div className="mb-8">
                        <h3 className="text-[#EAEAEA] font-medium mb-2">Description</h3>
                        <p className="text-[#9CA3AF] text-sm leading-relaxed">
                            {product.description || "Experience elegance with this premium quality outfit designed for the modern woman."}
                        </p>
                    </div>

                    <div className="mb-8">
                        <h3 className="text-[#EAEAEA] font-medium mb-3">Color</h3>
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-full border border-white/20 bg-gradient-to-br from-purple-500 to-pink-500"></div>
                            <span className="text-[#9CA3AF] text-sm">{product.color || "Multicolor"}</span>
                        </div>
                    </div>

                    <div className="mb-8">
                        <div className="flex justify-between items-center mb-3">
                            <h3 className="text-[#EAEAEA] font-medium">Select Size</h3>
                            <button className="text-[#C9A227] text-xs hover:underline">Size Chart</button>
                        </div>
                        <div className="flex flex-wrap gap-3">
                            {product.sizes?.map((size) => (
                                <button
                                    key={size}
                                    onClick={() => setSelectedSize(size)}
                                    className={`w-12 h-12 rounded-lg border flex items-center justify-center transition-all ${selectedSize === size
                                            ? "border-[#C9A227] bg-[#C9A227] text-black font-semibold shadow-lg shadow-[#C9A227]/20"
                                            : "border-[#262626] text-[#EAEAEA] hover:border-[#C9A227]"
                                        }`}
                                >
                                    {size}
                                </button>
                            ))}
                        </div>
                        {!selectedSize && <p className="text-red-500 text-xs mt-2">* Please select a size</p>}
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-4 mt-auto">
                        <div className="flex items-center gap-4">
                            <div className="flex items-center border border-[#262626] rounded-full">
                                <button
                                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                                    className="p-3 text-[#EAEAEA] hover:text-[#C9A227]"
                                >
                                    <Minus className="w-4 h-4" />
                                </button>
                                <span className="w-8 text-center text-[#EAEAEA] font-medium">{quantity}</span>
                                <button
                                    onClick={() => setQuantity(quantity + 1)}
                                    className="p-3 text-[#EAEAEA] hover:text-[#C9A227]"
                                >
                                    <Plus className="w-4 h-4" />
                                </button>
                            </div>
                        </div>

                        <div className="flex gap-4">
                            <button className="flex-1 py-4 bg-[#C9A227] text-black font-semibold rounded-xl hover:bg-white transition-colors shadow-lg flex items-center justify-center gap-2">
                                <ShoppingBag className="w-5 h-5" />
                                Add to Cart
                            </button>
                            <button className="p-4 border border-[#262626] rounded-xl text-[#EAEAEA] hover:border-red-500 hover:text-red-500 transition-colors">
                                <Heart className="w-6 h-6" />
                            </button>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}
