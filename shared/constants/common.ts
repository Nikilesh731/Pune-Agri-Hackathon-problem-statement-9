/**
 * Common Constants
 * Purpose: General constants used across the application
 */

// Date and Time
export const DATE_FORMATS = {
  DISPLAY: 'dd MMM yyyy',
  DISPLAY_WITH_TIME: 'dd MMM yyyy, HH:mm',
  ISO: 'yyyy-MM-dd',
  ISO_WITH_TIME: 'yyyy-MM-dd HH:mm:ss',
  API: 'yyyy-MM-ddTHH:mm:ss.SSSZ',
} as const

// Currency
export const CURRENCY = {
  CODE: 'INR',
  SYMBOL: '₹',
  DECIMAL_PLACES: 2,
} as const

// Language codes
export const LANGUAGES = {
  ENGLISH: 'en',
  HINDI: 'hi',
  BENGALI: 'bn',
  TAMIL: 'ta',
  TELUGU: 'te',
  MARATHI: 'mr',
  GUJARATI: 'gu',
  KANNADA: 'kn',
} as const

// Indian States
export const INDIAN_STATES = [
  'Andhra Pradesh',
  'Arunachal Pradesh',
  'Assam',
  'Bihar',
  'Chhattisgarh',
  'Goa',
  'Gujarat',
  'Haryana',
  'Himachal Pradesh',
  'Jharkhand',
  'Karnataka',
  'Kerala',
  'Madhya Pradesh',
  'Maharashtra',
  'Manipur',
  'Meghalaya',
  'Mizoram',
  'Nagaland',
  'Odisha',
  'Punjab',
  'Rajasthan',
  'Sikkim',
  'Tamil Nadu',
  'Telangana',
  'Tripura',
  'Uttar Pradesh',
  'Uttarakhand',
  'West Bengal',
] as const

// Agricultural Categories
export const CROP_CATEGORIES = [
  'Cereals',
  'Pulses',
  'Oilseeds',
  'Vegetables',
  'Fruits',
  'Spices',
  'Commercial Crops',
  'Plantation Crops',
  'Horticulture',
] as const

// Common crop names
export const COMMON_CROPS = [
  'Rice',
  'Wheat',
  'Maize',
  'Bajra',
  'Jowar',
  'Gram',
  'Tur',
  'Urad',
  'Moong',
  'Groundnut',
  'Mustard',
  'Soybean',
  'Cotton',
  'Sugarcane',
  'Potato',
  'Onion',
  'Tomato',
  'Brinjal',
  'Chilly',
  'Mango',
  'Banana',
] as const

// Land measurement units
export const LAND_UNITS = {
  HECTARE: {
    name: 'Hectare',
    symbol: 'ha',
    conversion_to_acre: 2.47105,
  },
  ACRE: {
    name: 'Acre',
    symbol: 'ac',
    conversion_to_hectare: 0.404686,
  },
  BIGHA: {
    name: 'Bigha',
    symbol: 'bigha',
    conversion_to_acre: 0.625, // Varies by region, using average
  },
  SQUARE_METERS: {
    name: 'Square Meters',
    symbol: 'm²',
    conversion_to_hectare: 0.0001,
  },
} as const

// Document types
export const DOCUMENT_TYPES = [
  'Aadhaar Card',
  'PAN Card',
  'Voter ID',
  'Driving License',
  'Passport',
  'Land Record',
  'Income Certificate',
  'Caste Certificate',
  'Bank Passbook',
  'Kisan Credit Card',
  'Crop Insurance Policy',
  'Educational Certificate',
  'Medical Certificate',
] as const

// Bank account types
export const BANK_ACCOUNT_TYPES = [
  'Savings Account',
  'Current Account',
  'Fixed Deposit',
  'Recurring Deposit',
] as const

// Irrigation sources
export const IRRIGATION_SOURCES = [
  'Well',
  'Tube Well',
  'Canal',
  'Tank',
  'Drip Irrigation',
  'Sprinkler Irrigation',
  'Rain-fed',
  'Other',
] as const

// Farm equipment types
export const EQUIPMENT_TYPES = [
  'Tractor',
  'Power Tiller',
  'Harvester',
  'Thresher',
  'Pump Set',
  'Sprayer',
  'Plough',
  'Cultivator',
  'Seed Drill',
  'Other',
] as const

// Subsidy schemes
export const SUBSIDY_SCHEMES = [
  'PM-Kisan Samman Nidhi',
  'Pradhan Mantri Fasal Bima Yojana',
  'Soil Health Card Scheme',
  'National Mission on Oilseeds and Oil Palm',
  'Paramparagat Krishi Vikas Yojana',
  'National Food Security Mission',
  'Rashtriya Krishi Vikas Yojana',
  'E-NAM',
  'Other State Schemes',
] as const

// Common validation patterns
export const PATTERNS = {
  AADHAAR: /^\d{12}$/,
  PAN: /^[A-Z]{5}\d{4}[A-Z]{1}$/,
  PHONE: /^\d{10}$/,
  PINCODE: /^\d{6}$/,
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  IFSC: /^[A-Z]{4}0[A-Z0-9]{6}$/,
  ACCOUNT_NUMBER: /^\d{9,18}$/,
  VOTER_ID: /^[A-Z]{3}\d{7}$/,
  DRIVING_LICENSE: /^[A-Z]{2}\d{2}\d{4}\d{7}$/,
} as const
