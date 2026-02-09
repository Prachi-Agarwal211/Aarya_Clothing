"use client";

import Image from "next/image";
import { Heart, ShoppingBag } from "lucide-react";

interface ProductCardProps {
    id: number | string;
    name: string;
    price: number;
    image: string;
    category?: string;
}

export default function ProductCard({ id, name, price, image, category }: ProductCardProps) {
    return (
        <div className="group relative bg-[#151517] rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition duration-500">
            {/* Image Container */}
            <div className="aspect-square relative overflow-hidden">
                <Image
                    src={image}
                    alt={name}
                    fill
                    className="object-cover transition-transform duration-700 group-hover:scale-110"
                />

                {/* Overlay on Hover */}
                <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

                {/* Quick Actions */}
                <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-3 opacity-0 group-hover:opacity-100 transform translate-y-4 group-hover:translate-y-0 transition-all duration-300">
                    <button className="p-3 bg-white text-black rounded-full hover:bg-[#C9A227] hover:text-white transition-colors shadow-lg">
                        <ShoppingBag className="w-5 h-5" />
                    </button>
                    <button className="p-3 bg-white text-black rounded-full hover:bg-red-500 hover:text-white transition-colors shadow-lg">
                        <Heart className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* Product Info */}
            <div className="p-5">
                <h3 className="text-base font-medium text-[#EAEAEA] mb-1 truncate font-sans">{name}</h3>
                {category && <p className="text-xs text-[#9CA3AF] mb-2">{category}</p>}
                <div className="flex items-center justify-between mt-2">
                    <span className="text-lg font-semibold text-[#C9A227]">₹{price.toLocaleString('en-IN')}</span>
                </div>
            </div>
        </div>
    );
}
