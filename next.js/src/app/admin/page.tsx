"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Users, Package, ShoppingBag, TrendingUp, Settings, LogOut, Menu, X, Home, Edit, Trash2, Plus } from "lucide-react";
import Link from "next/link";
import { uploadImageToR2 } from "@/lib/r2-upload";

export default function AdminDashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('dashboard');
  const router = useRouter();

  // Landing page categories state
  const [categories, setCategories] = useState([
    { id: 1, title: 'Kurtis set', image: '/placeholder-women.jpg', order: 1 },
    { id: 2, title: 'Cord Sets', image: '/placeholder-new.jpg', order: 2 },
    { id: 3, title: 'Gowns', image: '/placeholder-men.jpg', order: 3 },
    { id: 4, title: 'Sarees', image: '/placeholder-ethnic.jpg', order: 4 },
    { id: 5, title: 'Kurtis', image: '/placeholder-western.jpg', order: 5 },
    { id: 6, title: 'Duppata', image: '/placeholder-wedding.jpg', order: 6 },
  ]);

  const [draggedCategory, setDraggedCategory] = useState<any>(null);
  const [editingCategory, setEditingCategory] = useState<any>(null);
  const [newTitle, setNewTitle] = useState('');
  const [newImage, setNewImage] = useState('');
  const [dragOverCategory, setDragOverCategory] = useState<number | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [originalCategories, setOriginalCategories] = useState<any[]>([]);

  // Initialize original categories on component mount
  useEffect(() => {
    setOriginalCategories([
      { id: 1, title: 'Kurtis set', image: '/placeholder-women.jpg', order: 1 },
      { id: 2, title: 'Cord Sets', image: '/placeholder-new.jpg', order: 2 },
      { id: 3, title: 'Gowns', image: '/placeholder-men.jpg', order: 3 },
      { id: 4, title: 'Sarees', image: '/placeholder-ethnic.jpg', order: 4 },
      { id: 5, title: 'Kurtis', image: '/placeholder-western.jpg', order: 5 },
      { id: 6, title: 'Duppata', image: '/placeholder-wedding.jpg', order: 6 },
    ]);
  }, []);

  const handleLogout = () => {
    // Clear user session
    localStorage.removeItem('user');
    // Redirect to landing page
    router.push('/');
  };

  // Drag and drop handlers for reordering
  const handleDragStart = (e: React.DragEvent, category: any) => {
    setDraggedCategory(category);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, targetCategory: any) => {
    e.preventDefault();
    if (!draggedCategory || draggedCategory.id === targetCategory.id) return;

    const newCategories = [...categories];
    const draggedIndex = newCategories.findIndex(cat => cat.id === draggedCategory.id);
    const targetIndex = newCategories.findIndex(cat => cat.id === targetCategory.id);

    // Reorder categories
    newCategories.splice(draggedIndex, 1);
    newCategories.splice(targetIndex, 0, draggedCategory);

    // Update order numbers
    newCategories.forEach((cat, index) => {
      cat.order = index + 1;
    });

    setCategories(newCategories);
    setDraggedCategory(null);
  };

  // File drag and drop handlers for image uploads
  const handleFileDragOver = (e: React.DragEvent, categoryId: number) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOverCategory(categoryId);
    e.dataTransfer.dropEffect = 'copy';
  };

  const handleFileDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOverCategory(null);
  };

  const handleFileDrop = async (e: React.DragEvent, categoryId: number) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOverCategory(null);

    const files = e.dataTransfer.files;
    if (files.length === 0) return;

    const file = files[0];
    
    // Check if it's an image file
    if (!file.type.startsWith('image/')) {
      alert('Please drop an image file (jpg, png, gif, etc.)');
      return;
    }

    try {
      // Show loading state
      const loadingMessage = document.createElement('div');
      loadingMessage.textContent = 'Uploading image to Cloudflare R2...';
      loadingMessage.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #1A1A1A;
        color: #D4AF37;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #D4AF37;
        z-index: 9999;
        font-family: Arial, sans-serif;
      `;
      document.body.appendChild(loadingMessage);
      
      // Upload to R2
      const imageUrl = await uploadImageToR2(file);
      
      // Remove loading message
      document.body.removeChild(loadingMessage);
      
      // Update the category with the new R2 URL
      setCategories(categories.map(cat => 
        cat.id === categoryId 
          ? { ...cat, image: imageUrl }
          : cat
      ));

      alert(`Image uploaded successfully!\n\nURL: ${imageUrl}\n\nThe image will now appear on the landing page.`);
    } catch (error) {
      // Remove loading message if it exists
      const loadingMessage = document.querySelector('div[style*="position: fixed"]');
      if (loadingMessage) {
        document.body.removeChild(loadingMessage);
      }
      
      alert('Failed to upload image. Please check your R2 configuration and try again.');
      console.error('Upload error:', error);
    }
  };

  // Category management functions
  const handleEditCategory = (category: any) => {
    setEditingCategory(category);
    setNewTitle(category.title);
    setNewImage(category.image);
  };

  const handleSaveCategory = () => {
    if (!editingCategory) return;

    setCategories(categories.map(cat => 
      cat.id === editingCategory.id 
        ? { ...cat, title: newTitle, image: newImage }
        : cat
    ));

    setEditingCategory(null);
    setNewTitle('');
    setNewImage('');
  };

  const handleCancelEdit = () => {
    setEditingCategory(null);
    setNewTitle('');
    setNewImage('');
  };

  const handleSaveToLocalStorage = () => {
    // Store original categories on first save attempt
    if (originalCategories.length === 0) {
      setOriginalCategories([...categories]);
    }
    setShowConfirmModal(true);
  };

  const getChanges = () => {
    const changes: any[] = [];
    
    categories.forEach((category, index) => {
      const original = originalCategories.find(orig => orig.id === category.id);
      
      if (!original) {
        changes.push({
          type: 'new',
          category: category.title,
          details: `New category added at position ${index + 1}`
        });
      } else {
        const categoryChanges = [];
        
        if (original.title !== category.title) {
          categoryChanges.push(`Title: "${original.title}" → "${category.title}"`);
        }
        
        if (original.image !== category.image) {
          categoryChanges.push(`Image: "${original.image}" → "${category.image}"`);
        }
        
        if (original.order !== category.order) {
          categoryChanges.push(`Position: ${original.order} → ${category.order}`);
        }
        
        if (categoryChanges.length > 0) {
          changes.push({
            type: 'modified',
            category: category.title,
            details: categoryChanges.join(', ')
          });
        }
      }
    });
    
    return changes;
  };

  const confirmSave = () => {
    localStorage.setItem('landingCategories', JSON.stringify(categories));
    setOriginalCategories([...categories]);
    setShowConfirmModal(false);
    
    // Dispatch custom event to notify landing page of changes
    window.dispatchEvent(new CustomEvent('categoriesUpdated', { 
      detail: { categories } 
    }));
    
    alert('Categories saved successfully! Landing page will update automatically.');
  };

  const cancelSave = () => {
    setShowConfirmModal(false);
  };

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'landing', label: 'Landing Page', icon: Home },
    { id: 'products', label: 'Products', icon: Package },
    { id: 'orders', label: 'Orders', icon: ShoppingBag },
    { id: 'customers', label: 'Customers', icon: Users },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const stats = [
    { label: 'Total Products', value: '156', change: '+12%', trend: 'up' },
    { label: 'Total Orders', value: '1,234', change: '+8%', trend: 'up' },
    { label: 'Total Customers', value: '892', change: '+15%', trend: 'up' },
    { label: 'Revenue', value: '$45,678', change: '+23%', trend: 'up' },
  ];

  const recentOrders = [
    { id: '#1234', customer: 'John Doe', product: 'Kurti Set', amount: '$89.99', status: 'completed' },
    { id: '#1235', customer: 'Jane Smith', product: 'Saree', amount: '$129.99', status: 'processing' },
    { id: '#1236', customer: 'Mike Johnson', product: 'Gown', amount: '$199.99', status: 'pending' },
    { id: '#1237', customer: 'Sarah Wilson', product: 'Cord Set', amount: '$79.99', status: 'completed' },
  ];

  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return (
          <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {stats.map((stat, index) => (
                <div key={index} className="bg-[#1A1A1A] p-6 rounded-xl border border-[#D4AF37]/20">
                  <h3 className="text-sm font-medium text-[#B89C5A] mb-2">{stat.label}</h3>
                  <p className="text-2xl font-bold text-[#F4EDE4] mb-2">{stat.value}</p>
                  <div className="flex items-center text-sm">
                    <span className={`text-green-400 ${stat.trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
                      {stat.change}
                    </span>
                    <span className="text-[#B89C5A] ml-2">from last month</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Recent Orders */}
            <div className="bg-[#1A1A1A] rounded-xl border border-[#D4AF37]/20">
              <div className="p-6 border-b border-[#D4AF37]/20">
                <h2 className="text-lg font-semibold text-[#F4EDE4]">Recent Orders</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-[#0E0E0E]">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[#B89C5A] uppercase tracking-wider">Order ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[#B89C5A] uppercase tracking-wider">Customer</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[#B89C5A] uppercase tracking-wider">Product</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[#B89C5A] uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[#B89C5A] uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#D4AF37]/10">
                    {recentOrders.map((order, index) => (
                      <tr key={index} className="hover:bg-[#0E0E0E]/50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[#F4EDE4]">{order.id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[#F4EDE4]">{order.customer}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[#F4EDE4]">{order.product}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[#F4EDE4]">{order.amount}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            order.status === 'completed' ? 'bg-green-900/30 text-green-400' :
                            order.status === 'processing' ? 'bg-yellow-900/30 text-yellow-400' :
                            'bg-red-900/30 text-red-400'
                          }`}>
                            {order.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        );

      case 'landing':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-[#F4EDE4]">Landing Page Categories</h2>
              <button
                onClick={handleSaveToLocalStorage}
                className="btn-gold"
              >
                Save Changes
              </button>
            </div>
            
            <div className="bg-[#1A1A1A] rounded-xl border border-[#D4AF37]/20 p-6">
              <p className="text-[#B89C5A] mb-6">
                Drag and drop categories to reorder. Click edit to modify title and image.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {categories.sort((a, b) => a.order - b.order).map((category) => (
                  <div
                    key={category.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, category)}
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDrop(e, category)}
                    className="bg-[#0E0E0E] border border-[#D4AF37]/20 rounded-lg p-4 cursor-move hover:border-[#D4AF37]/50 transition-colors"
                  >
                    {editingCategory?.id === category.id ? (
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                            Title
                          </label>
                          <input
                            type="text"
                            value={newTitle}
                            onChange={(e) => setNewTitle(e.target.value)}
                            className="w-full px-3 py-2 bg-[#1A1A1A] border border-[#D4AF37]/20 rounded text-[#F4EDE4] focus:outline-none focus:border-[#D4AF37]"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-[#F4EDE4] mb-2">
                            Image Path
                          </label>
                          <input
                            type="text"
                            value={newImage}
                            onChange={(e) => setNewImage(e.target.value)}
                            className="w-full px-3 py-2 bg-[#1A1A1A] border border-[#D4AF37]/20 rounded text-[#F4EDE4] focus:outline-none focus:border-[#D4AF37]"
                          />
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={handleSaveCategory}
                            className="flex-1 py-2 bg-[#D4AF37] text-black rounded font-medium hover:bg-[#C9A24D] transition-colors"
                          >
                            Save
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            className="flex-1 py-2 bg-[#1A1A1A] border border-[#D4AF37]/20 text-[#F4EDE4] rounded font-medium hover:bg-[#0E0E0E] transition-colors"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div
                          className={`aspect-[4/5] bg-gradient-to-br from-[#2A2A2A] to-[#1A1A1A] rounded-lg mb-4 flex items-center justify-center relative overflow-hidden cursor-pointer ${
                            dragOverCategory === category.id ? 'ring-2 ring-[#D4AF37]' : ''
                          }`}
                          onDragOver={(e) => handleFileDragOver(e, category.id)}
                          onDragLeave={handleFileDragLeave}
                          onDrop={(e) => handleFileDrop(e, category.id)}
                        >
                          {category.image && (category.image.startsWith('blob:') || category.image.startsWith('https://pub-')) ? (
                            <img 
                              src={category.image} 
                              alt={category.title}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="text-center">
                              <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-[#D4AF37]/10 flex items-center justify-center">
                                <span className="text-2xl text-[#D4AF37]">👗</span>
                              </div>
                              <p className="text-xs text-[#B89C5A]">{category.image}</p>
                            </div>
                          )}
                          {dragOverCategory === category.id && (
                            <div className="absolute inset-0 bg-[#D4AF37]/20 flex items-center justify-center">
                              <div className="text-center">
                                <p className="text-white font-medium">Drop image here</p>
                                <p className="text-white/80 text-sm">to update category</p>
                              </div>
                            </div>
                          )}
                        </div>
                        <h3 className="text-lg font-semibold text-[#F4EDE4] mb-2">{category.title}</h3>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEditCategory(category)}
                            className="flex-1 py-2 bg-[#D4AF37]/20 text-[#D4AF37] rounded text-sm font-medium hover:bg-[#D4AF37]/30 transition-colors"
                          >
                            Edit
                          </button>
                        </div>
                        <p className="text-xs text-[#B89C5A] mt-2 text-center">
                          💡 Drag image file here to update
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'products':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-[#F4EDE4]">Products</h2>
              <button className="btn-gold flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Add Product
              </button>
            </div>
            <div className="bg-[#1A1A1A] rounded-xl border border-[#D4AF37]/20 p-6">
              <p className="text-[#B89C5A]">Product management interface will be implemented here.</p>
            </div>
          </div>
        );

      case 'orders':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-[#F4EDE4]">Orders</h2>
            <div className="bg-[#1A1A1A] rounded-xl border border-[#D4AF37]/20 p-6">
              <p className="text-[#B89C5A]">Order management interface will be implemented here.</p>
            </div>
          </div>
        );

      case 'customers':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-[#F4EDE4]">Customers</h2>
            <div className="bg-[#1A1A1A] rounded-xl border border-[#D4AF37]/20 p-6">
              <p className="text-[#B89C5A]">Customer management interface will be implemented here.</p>
            </div>
          </div>
        );

      case 'analytics':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-[#F4EDE4]">Analytics</h2>
            <div className="bg-[#1A1A1A] rounded-xl border border-[#D4AF37]/20 p-6">
              <p className="text-[#B89C5A]">Analytics dashboard will be implemented here.</p>
            </div>
          </div>
        );

      case 'settings':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-[#F4EDE4]">Settings</h2>
            <div className="bg-[#1A1A1A] rounded-xl border border-[#D4AF37]/20 p-6">
              <p className="text-[#B89C5A]">Settings interface will be implemented here.</p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-[#0E0E0E]">
      {/* Header */}
      <header className="bg-[#1A1A1A] border-b border-[#D4AF37]/20">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden p-2 text-[#F4EDE4] hover:text-[#D4AF37]"
              >
                {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
              <h1 className="ml-4 text-xl font-bold text-[#D4AF37]">Admin Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-[#F4EDE4]">Admin User</span>
              <button 
                onClick={handleLogout}
                className="p-2 text-[#F4EDE4] hover:text-[#D4AF37]"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`${sidebarOpen ? 'block' : 'hidden'} md:block w-64 bg-[#1A1A1A] min-h-screen border-r border-[#D4AF37]/20`}>
          <nav className="p-4 space-y-2">
            {menuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  activeSection === item.id
                    ? 'bg-[#D4AF37]/20 text-[#D4AF37]'
                    : 'text-[#F4EDE4] hover:bg-[#0E0E0E] hover:text-[#D4AF37]'
                }`}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {renderContent()}
        </main>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#1A1A1A] border border-[#D4AF37]/20 rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-[#F4EDE4] mb-4">Confirm Changes</h3>
            
            <div className="mb-6">
              <p className="text-[#B89C5A] mb-4">Please review the following changes before saving:</p>
              
              {getChanges().length === 0 ? (
                <p className="text-[#F4EDE4] bg-[#0E0E0E] p-4 rounded-lg">
                  No changes detected.
                </p>
              ) : (
                <div className="space-y-3">
                  {getChanges().map((change, index) => (
                    <div key={index} className="bg-[#0E0E0E] p-4 rounded-lg border-l-4 border-[#D4AF37]">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-1 text-xs rounded ${
                          change.type === 'new' 
                            ? 'bg-green-900/30 text-green-400' 
                            : 'bg-blue-900/30 text-blue-400'
                        }`}>
                          {change.type === 'new' ? 'NEW' : 'MODIFIED'}
                        </span>
                        <span className="font-medium text-[#F4EDE4]">{change.category}</span>
                      </div>
                      <p className="text-sm text-[#B89C5A]">{change.details}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-4">
              <button
                onClick={confirmSave}
                className="flex-1 py-3 bg-[#D4AF37] text-black rounded-lg font-medium hover:bg-[#C9A24D] transition-colors"
              >
                Confirm & Save
              </button>
              <button
                onClick={cancelSave}
                className="flex-1 py-3 bg-[#0E0E0E] border border-[#D4AF37]/20 text-[#F4EDE4] rounded-lg font-medium hover:bg-[#1A1A1A] transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
