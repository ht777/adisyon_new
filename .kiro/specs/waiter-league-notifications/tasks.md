# Implementation Plan

## 1. Backend - Garson Ligi Puan Sistemi

- [x] 1.1 Verify and fix waiter score increment on order creation
  - Review `create_order` in `backend/routers/orders.py`
  - Ensure UserStats.total_orders increments by 1 when waiter_id is present
  - Create UserStats record if not exists
  - _Requirements: 1.1_

- [x] 1.2 Verify and fix waiter score decrement on order cancellation
  - Review `update_order_status` in `backend/routers/orders.py`
  - Ensure UserStats.total_orders decrements by 1 when order is cancelled
  - Ensure total_orders never goes below 0
  - _Requirements: 1.2, 1.3_

- [ ]* 1.3 Write property test for waiter score system
  - **Property 1: Order submission increments waiter score**
  - **Property 2: Order cancellation decrements waiter score (non-negative)**
  - **Validates: Requirements 1.1, 1.2, 1.3**

## 2. Backend - League API

- [x] 2.1 Create or update league endpoint in admin router
  - Add `GET /api/admin/league` endpoint in `backend/routers/admin.py`
  - Return waiters with user_id, username, full_name, total_orders
  - Sort by total_orders DESC
  - Remove tip-related data from response
  - _Requirements: 1.4, 1.5, 2.1, 2.2_

- [ ]* 2.2 Write property test for league sorting
  - **Property 3: League sorting by score**
  - **Validates: Requirements 1.4**

## 3. Frontend - Bildirim Paneli

- [x] 3.1 Add notification panel to dashboard header
  - Add notification container in header area of `frontend/static/admin.html`
  - Style with fixed position in header bar
  - Add notification counter badge
  - _Requirements: 3.1, 3.2, 5.3_

- [x] 3.2 Implement notification rendering with delete buttons
  - Create `renderNotifications()` function
  - Show table name, type icon, timestamp for each notification
  - Add delete button next to each notification
  - Use orange/amber for waiter_call, purple for bill_request
  - _Requirements: 3.3, 3.4, 4.1, 5.1, 5.2_

- [x] 3.3 Implement notification state management
  - Create notifications array to store active notifications
  - Implement `addNotification()` function
  - Implement `deleteNotification(id)` function
  - Generate unique IDs for each notification
  - _Requirements: 4.2, 4.3, 4.4, 5.4_

- [x] 3.4 Update WebSocket handler for notifications
  - Modify `connectWS()` to call `addNotification()` for waiter_call and bill_request
  - Keep audio alert functionality
  - Remove toast-only display, use persistent panel instead
  - _Requirements: 3.1, 3.2, 3.5_

- [ ]* 3.5 Write property test for notification system
  - **Property 4: Notification delivery for customer calls**
  - **Property 5: Notification deletion preserves other notifications**
  - **Property 6: Notification accumulation**
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 4.2, 4.3, 5.4**

## 4. Frontend - Garson Ligi Güncelleme

- [x] 4.1 Update loadLeague() function
  - Fetch from `/api/admin/league` endpoint
  - Remove tip column from table
  - Display only username/full_name and total_orders (puan)
  - Sort display by puan descending
  - _Requirements: 1.4, 1.5, 2.1_

- [x] 4.2 Update league section HTML
  - Remove tip-related table headers
  - Update column structure: Sıra, Kullanıcı, Puan
  - Add visual ranking indicators (gold, silver, bronze for top 3)
  - _Requirements: 1.5, 2.1_

## 5. Checkpoint

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## 6. Final Integration

- [ ] 6.1 Test end-to-end flow
  - Test order creation increments waiter score
  - Test order cancellation decrements waiter score
  - Test notification appears when customer calls waiter
  - Test notification appears when customer requests bill
  - Test notification deletion works correctly
  - Test league displays correct sorted data
  - _Requirements: All_
