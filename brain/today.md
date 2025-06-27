# 💰 Payment Integration Implementation Plan (UPDATED)
*Date: 2025-01-27*

## **Overview**
Implement 7-day free trial subscription system with separate signup/signin flows, name collection, and complete Stripe integration including customer portal.

---

## 🎯 **High-Level Changes Required**

### **What We're Changing:**
- **Split Auth**: Single `/auth` page → Separate `/signup` and `/signin` pages
- **Name Collection**: Add first name field during signup only
- **Payment Flow**: New users → Stripe checkout after verification
- **Stripe Integration**: Full setup with Price ID, webhooks, and customer portal
- **Subscription Context**: Track trial status, plan details, billing dates
- **Account Management**: Stripe-hosted billing portal for users

---

## 📋 **Step-by-Step Implementation Process**

### **Phase 1: Create New Pages (Frontend)**

#### **Step 1: Create Signup Page**
```
📁 web/src/app/signup/page.tsx (NEW FILE)
```
- Form with: First Name + Email fields
- Stores name temporarily in localStorage
- Sends magic link with `shouldCreateUser: true`

#### **Step 2: Create Signin Page** 
```
📁 web/src/app/signin/page.tsx (NEW FILE)  
```
- Form with: Email only
- Sends magic link with `shouldCreateUser: false`

#### **Step 3: Update Verification Page**
```
📁 web/src/features/auth/MagicLinkForm.tsx (MODIFY EXISTING)
```
- Check if signup vs signin (URL parameter)
- If signup: Save name to profile + redirect to payment
- If signin: Check subscription + redirect accordingly

### **Phase 2: Update Database (Backend)**

#### **Step 4: Update Database Trigger**
```sql
-- Modify existing trigger to:
-- 1. Save name from user metadata to profiles table
-- 2. Create subscription record for new users (7-day trial)
```

### **Phase 2.5: Stripe Infrastructure Setup**

#### **Step 5: Install Stripe Packages**
```bash
npm install stripe @stripe/stripe-js
```

#### **Step 6: Environment Variables Setup**
```env
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_...
STRIPE_PRICE_ID=price_... (YOU CREATE THIS IN STRIPE DASHBOARD)
```

#### **Step 7: Create Subscription Context**
```
📁 web/src/features/subscription/SubscriptionProvider.tsx (NEW FILE)
```
- Track subscription status, trial end date, plan details
- Similar to AuthContext but for billing
- Fetch subscription data from Supabase

### **Phase 3: Add Payment Flow (Frontend)**

#### **Step 8: Create Checkout Page**
```
📁 web/src/app/checkout/page.tsx (NEW FILE)
```
- Creates Stripe session using YOUR Price ID
- Redirects to Stripe payment with 7-day trial

#### **Step 9: Add Stripe API Routes**
```
📁 web/src/app/api/stripe/create-checkout-session/route.ts (NEW FILE)
📁 web/src/app/api/stripe/webhook/route.ts (NEW FILE)
📁 web/src/app/api/stripe/customer-portal/route.ts (NEW FILE)
```

### **Phase 4: Account Management**

#### **Step 10: Create Account Page**
```
📁 web/src/app/account/page.tsx (NEW FILE)
```
- Display subscription status, trial end date
- "Manage Subscription" button → Stripe Customer Portal
- Cancel, update payment, view invoices (all handled by Stripe)

### **Phase 5: Update Navigation & Pricing**

#### **Step 11: Create/Update Pricing Page**
```
📁 web/src/app/pricing/page.tsx (CREATE OR MODIFY)
```
- Pricing table on homepage/landing page
- "Start Free Trial" button → `/signup`

#### **Step 12: Update Links**
- Pricing page → `/signup` (not `/auth`)
- Add "Sign In" links pointing to `/signin`
- Remove old `/auth` page
- Add account management in user nav

---

## 🔄 **Complete User Flow**

### **New User Journey:**
```
Homepage/Pricing Table
    ↓ "Start Free Trial"
/signup (first name + email)
    ↓ Magic Link Verification
/checkout (Stripe with YOUR Price ID)
    ↓ 7-Day Trial + Payment Setup
/chat (with active subscription context)

Later: /account → "Manage Subscription" → Stripe Portal
```

### **Existing User Journey:**
```
Homepage/Any Page
    ↓ "Sign In"
/signin (email only)
    ↓ Magic Link Verification
/chat (subscription context loaded)

Account Management: /account → Stripe Portal
```

---

## 🛠️ **Files to Create/Modify**

### **NEW FILES:**
- `web/src/app/signup/page.tsx`
- `web/src/app/signin/page.tsx` 
- `web/src/app/checkout/page.tsx`
- `web/src/app/account/page.tsx`
- `web/src/app/pricing/page.tsx` (if not exists)
- `web/src/features/subscription/SubscriptionProvider.tsx`
- `web/src/app/api/stripe/create-checkout-session/route.ts`
- `web/src/app/api/stripe/webhook/route.ts`
- `web/src/app/api/stripe/customer-portal/route.ts`

### **MODIFY EXISTING:**
- `web/src/features/auth/MagicLinkForm.tsx` (verification logic)
- `web/src/app/layout.tsx` (add SubscriptionProvider wrapper)
- `web/src/components/navigation/UserNav.tsx` (add account link)
- `web/package.json` (add Stripe dependencies)
- Database trigger function (add subscription creation)

### **REMOVE:**
- `web/src/app/auth/page.tsx` (old combined page)

---

## ⏱️ **Updated Time Estimate**

1. **Phase 1** (Split pages): ~2-3 hours
2. **Phase 2** (Database): ~1 hour  
3. **Phase 2.5** (Stripe Setup): ~2-3 hours
4. **Phase 3** (Payment Flow): ~4-5 hours
5. **Phase 4** (Account Management): ~2-3 hours
6. **Phase 5** (Navigation/Pricing): ~1-2 hours

**Total**: ~12-17 hours of work

---

## 🔧 **Stripe Setup Requirements**

### **What YOU Need to Create in Stripe Dashboard:**
1. **Product**: "Grizz Pro Subscription"
2. **Price**: $10/month recurring with 7-day trial
3. **Price ID**: Copy this for environment variables
4. **Webhook Endpoint**: Point to your domain/api/stripe/webhook

### **What WE Need to Code:**
- Checkout session creation using your Price ID
- Webhook handling for subscription events
- Customer portal session creation
- Subscription context management

---

## 🔑 **Key Features**

- ✅ Collect user names during signup
- ✅ Clean separation of signup vs signin
- ✅ Automatic payment flow with 7-day trial
- ✅ Stripe-hosted customer portal (cancel, update, invoices)
- ✅ Subscription context throughout app
- ✅ Keep magic link simplicity
- ✅ Complete account management
- ✅ Pricing table integration

---

## 🚀 **Next Steps**

1. **YOU**: Create Stripe Price ID and share it
2. **US**: Start with Phase 1 (separate pages)
3. Install Stripe packages and set up environment
4. Implement subscription context
5. Build checkout and account flows
6. Test end-to-end payment flow

---

## 📝 **Important Notes**

- **Stripe handles**: Payment processing, invoicing, customer portal UI
- **We handle**: User authentication, subscription status tracking, redirects
- **Database stores**: Subscription status, Stripe customer/subscription IDs
- **No free plan**: Everyone pays $10/month after 7-day trial
- **Trial period**: Managed by Stripe, not by us
