# Implementation Plan

- [x] 1. Database Model Updates




  - [ ] 1.1 Add payment_method field to Order model
    - Add `payment_method = Column(String, nullable=True)` to Order class in models.py

    - Values: "cash", "card", or None
    - _Requirements: 1.4_

  - [ ] 1.2 Add initial_stock field to Product model
    - Add `initial_stock = Column(Integer, default=0)` to Product class in models.py
    - _Requirements: 2.1_
  - [x] 1.3 Create Alembic migration for new fields




    - Create migration file in backend/alembic/versions/
    - Add payment_method to orders table
    - Add initial_stock to products table
    - _Requirements: 1.4, 2.1_

- [x] 2. Backend API Updates


  - [ ] 2.1 Update table close endpoint to accept payment_method
    - Modify POST /api/tables/close/{table_id} in tables.py router
    - Accept optional payment_method in request body
    - Store payment_method on all orders being closed for that table
    - _Requirements: 1.4_
  - [x]* 2.2 Write property test for payment method persistence

    - **Property 1: Payment method persistence**
    - **Validates: Requirements 1.4**
  - [ ] 2.3 Create critical stock endpoint
    - Add GET /api/admin/critical-stock endpoint in admin.py
    - Return products where track_stock=True and stock <= initial_stock * 0.2
    - Include product id, name, current_stock, initial_stock, percentage
    - _Requirements: 2.1_
  - [ ]* 2.4 Write property test for critical stock classification
    - **Property 3: Critical stock classification threshold**
    - **Validates: Requirements 2.1**




  - [ ] 2.5 Update reports/sales endpoint with payment breakdown
    - Modify GET /api/admin/reports/sales in admin.py



    - Add cash_total and card_total to response
    - Sum order totals grouped by payment_method
    - _Requirements: 1.5_
  - [x]* 2.6 Write property test for payment breakdown calculation

    - **Property 2: Payment breakdown sum equals total revenue**
    - **Validates: Requirements 1.5**


- [ ] 3. Checkpoint - Backend Tests
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Frontend CSS Updates
  - [x] 4.1 Add critical stock alert animation CSS

    - Add @keyframes criticalPulse animation to admin.html style section
    - Add .critical-stock-alert class with red flashing border

    - _Requirements: 2.3, 3.2_


- [ ] 5. Frontend Dashboard Updates
  - [x] 5.1 Add critical stock alerts section to Dashboard

    - Add new div for critical stock alerts after stat cards
    - Position above weekly sales chart
    - Include container with id="criticalStockAlertsDashboard"

    - _Requirements: 2.2, 2.3, 2.4, 2.5_

  - [ ] 5.2 Reorder Dashboard sections
    - Move open tables section above weekly sales chart
    - Order: Stats → Critical Stock Alerts → Open Tables → Weekly Chart

    - _Requirements: 4.1, 4.2_
  - [ ] 5.3 Add loadCriticalStockAlerts JavaScript function
    - Fetch from /api/admin/critical-stock


    - Render alert cards with product name and stock

    - Apply critical-stock-alert class for animation
    - Hide section if no critical products
    - _Requirements: 2.2, 2.3, 2.4, 2.5_
  - [ ] 5.4 Update loadDashboard to call loadCriticalStockAlerts
    - Call loadCriticalStockAlerts() in loadDashboard function
    - _Requirements: 2.2_

- [ ] 6. Frontend Stock Section Updates
  - [ ] 6.1 Add critical stock alerts section to Stock page
    - Add new div for critical stock alerts before stock table
    - Include container with id="criticalStockAlertsStock"
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  - [ ] 6.2 Update loadStock to refresh critical alerts
    - Call loadCriticalStockAlerts after stock table loads
    - Refresh alerts when stock is updated
    - _Requirements: 3.5_

- [ ] 7. Frontend Reports Updates
  - [ ] 7.1 Update reports revenue card HTML
    - Add cash_total and card_total display below total revenue
    - Use icons for visual distinction (💵 Nakit, 💳 Kredi Kartı)
    - _Requirements: 1.2, 1.3_
  - [ ] 7.2 Update loadReports JavaScript function
    - Parse cash_total and card_total from API response
    - Update revenue card with payment breakdown
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 8. Frontend Payment Modal Update
  - [ ] 8.1 Update confirmCloseTable function
    - Send payment_method parameter to close endpoint
    - Pass "cash" or "card" based on button clicked
    - _Requirements: 1.4_

- [ ] 9. Final Checkpoint
  - Ensure all tests pass, ask the user if questions arise.
