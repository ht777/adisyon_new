# Requirements Document

## Introduction

Bu özellik, restoran yönetim sisteminde garson performans takibi (garson ligi) ve müşteri bildirim sistemini kapsamaktadır. Garsonlar verdikleri her sipariş için puan kazanacak, iptal durumunda puan düşecektir. Müşteriler garson çağırdığında veya hesap istediğinde admin dashboard'da üst barda bildirimler görünecek ve bu bildirimler silinebilir olacaktır. Ayrıca mevcut bahşiş sistemi kaldırılacaktır.

## Glossary

- **Garson Ligi**: Garsonların sipariş performansını takip eden ve sıralayan sistem
- **Puan**: Her tamamlanan sipariş için garsona verilen 1 birimlik değer
- **Bildirim Paneli**: Dashboard üst barında görünen müşteri çağrı ve hesap isteme bildirimleri
- **Dashboard**: Admin yönetim paneli ana sayfası
- **WebSocket**: Gerçek zamanlı bildirim iletişimi için kullanılan protokol

## Requirements

### Requirement 1

**User Story:** As a restaurant manager, I want to track waiter performance based on orders, so that I can evaluate and reward top performers.

#### Acceptance Criteria

1. WHEN a waiter submits an order THEN the System SHALL increment that waiter's total_orders count by 1
2. WHEN an order is cancelled THEN the System SHALL decrement the associated waiter's total_orders count by 1
3. WHEN a waiter's total_orders count would become negative THEN the System SHALL set the count to 0
4. WHEN the league section is displayed THEN the System SHALL show all waiters sorted by total_orders in descending order
5. WHEN displaying waiter statistics THEN the System SHALL show the waiter's name and total order count (puan)

### Requirement 2

**User Story:** As a restaurant manager, I want to remove the tip tracking feature, so that the system focuses only on order-based performance.

#### Acceptance Criteria

1. WHEN the league section is displayed THEN the System SHALL NOT show any tip-related columns or data
2. WHEN waiter statistics are calculated THEN the System SHALL ignore tip-related fields

### Requirement 3

**User Story:** As a restaurant manager, I want to see customer call notifications in the dashboard header, so that I can respond quickly to customer needs.

#### Acceptance Criteria

1. WHEN a customer calls a waiter from the menu page THEN the System SHALL display a notification in the dashboard header bar
2. WHEN a customer requests the bill from the menu page THEN the System SHALL display a notification in the dashboard header bar
3. WHEN a notification is displayed THEN the System SHALL show the table number/name and notification type (waiter call or bill request)
4. WHEN a notification is displayed THEN the System SHALL show a timestamp indicating when the call was made
5. WHEN a notification is received THEN the System SHALL play an audio alert sound

### Requirement 4

**User Story:** As a restaurant manager, I want to dismiss notifications after viewing them, so that I can keep the notification area clean and organized.

#### Acceptance Criteria

1. WHEN a notification is displayed THEN the System SHALL show a delete button next to each notification
2. WHEN the delete button is clicked THEN the System SHALL remove that specific notification from the display
3. WHEN multiple notifications exist THEN the System SHALL allow individual deletion of each notification
4. WHEN all notifications are deleted THEN the System SHALL show an empty state or hide the notification panel

### Requirement 5

**User Story:** As a restaurant manager, I want notifications to be visually distinct, so that I can quickly identify the type of customer request.

#### Acceptance Criteria

1. WHEN a waiter call notification is displayed THEN the System SHALL use an orange/amber color scheme with a bell icon
2. WHEN a bill request notification is displayed THEN the System SHALL use a purple/blue color scheme with a payment icon
3. WHEN notifications are displayed THEN the System SHALL show them in a persistent panel in the header area
4. WHEN new notifications arrive THEN the System SHALL add them to the existing notification list without removing previous ones
