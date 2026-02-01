// Test Credentials for Aarya Clothings

export interface UserCredentials {
  email: string;
  password: string;
  role: 'admin' | 'customer';
  name: string;
  phone?: string;
}

export const TEST_CREDENTIALS: {
  admin: UserCredentials;
  customers: UserCredentials[];
} = {
  // Admin Credentials
  admin: {
    email: "admin@aaryaclothings.com",
    password: "Admin@1234",
    role: "admin",
    name: "Admin User"
  },
  
  // Customer Credentials
  customers: [
    {
      email: "customer1@aaryaclothings.com",
      password: "Customer@1234",
      role: "customer",
      name: "John Doe",
      phone: "+1234567890"
    },
    {
      email: "customer2@aaryaclothings.com", 
      password: "Customer@1234",
      role: "customer",
      name: "Jane Smith",
      phone: "+0987654321"
    },
    {
      email: "test@aaryaclothings.com",
      password: "Test@1234", 
      role: "customer",
      name: "Test User",
      phone: "+1122334455"
    }
  ]
};

// Authentication helper functions
export const authenticateUser = (email: string, password: string): {
  success: boolean;
  user?: UserCredentials;
  message?: string;
} => {
  // Check admin credentials
  if (email === TEST_CREDENTIALS.admin.email && password === TEST_CREDENTIALS.admin.password) {
    return {
      success: true,
      user: TEST_CREDENTIALS.admin
    };
  }
  
  // Check customer credentials
  const customer = TEST_CREDENTIALS.customers.find(
    cust => cust.email === email && cust.password === password
  );
  
  if (customer) {
    return {
      success: true,
      user: customer
    };
  }
  
  return {
    success: false,
    message: "Invalid email or password"
  };
};

// Get user by email
export const getUserByEmail = (email: string): UserCredentials | undefined => {
  if (email === TEST_CREDENTIALS.admin.email) {
    return TEST_CREDENTIALS.admin;
  }
  
  return TEST_CREDENTIALS.customers.find(cust => cust.email === email);
};
