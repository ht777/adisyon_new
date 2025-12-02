# Requirements Document

## Introduction

Bu özellik, restoran yönetim sistemine iki önemli iyileştirme ekler: (1) Raporlar bölümünde toplam ciro kutusuna nakit ve kredi kartı ödeme dağılımının gösterilmesi, (2) Dashboard ve Stok sekmelerine kritik stok seviyesi uyarılarının eklenmesi. Kritik stok uyarıları, stok miktarı başlangıç stoğunun %20'sine düştüğünde görsel olarak dikkat çekici şekilde (kırmızı yanıp sönen kenarlık) gösterilecektir.

## Glossary

- **Admin_Panel**: Restoran yöneticilerinin kullandığı web tabanlı yönetim arayüzü
- **Dashboard**: Admin panelindeki ana sayfa, genel istatistikleri ve grafikleri gösteren bölüm
- **Stok_Sekmesi**: Ürün stok miktarlarının yönetildiği admin panel bölümü
- **Raporlar_Sekmesi**: Satış ve ciro raporlarının görüntülendiği admin panel bölümü
- **Kritik_Stok**: Bir ürünün mevcut stok miktarının, o ürün için tanımlanan başlangıç stok miktarının %20'si veya altına düşmesi durumu
- **Ödeme_Yöntemi**: Siparişin kapatılma şekli (nakit veya kredi kartı)
- **Toplam_Ciro**: Belirli bir tarih aralığında tamamlanan siparişlerin toplam tutarı

## Requirements

### Requirement 1

**User Story:** As a restoran yöneticisi, I want to see the breakdown of total revenue by payment method (cash vs credit card), so that I can understand customer payment preferences and manage cash flow better.

#### Acceptance Criteria

1. WHEN the reports section loads THEN the Admin_Panel SHALL display the total revenue amount in the existing revenue card
2. WHEN the reports section loads THEN the Admin_Panel SHALL display the cash payment total below the total revenue
3. WHEN the reports section loads THEN the Admin_Panel SHALL display the credit card payment total below the cash payment total
4. WHEN an order is closed with a payment method THEN the system SHALL store the payment method (cash or card) with the order record
5. WHEN calculating payment breakdown THEN the system SHALL sum order totals grouped by payment method for the selected date range

### Requirement 2

**User Story:** As a restoran yöneticisi, I want to see critical stock alerts prominently on the Dashboard, so that I can quickly identify products that need restocking before they run out.

#### Acceptance Criteria

1. WHEN a product's current stock falls to 20% or below of its initial stock quantity THEN the system SHALL classify that product as Kritik_Stok
2. WHEN the Dashboard loads THEN the Admin_Panel SHALL display a critical stock alerts section above the weekly sales chart
3. WHEN Kritik_Stok products exist THEN the Admin_Panel SHALL display each critical product in a card with a red flashing border animation
4. WHEN Kritik_Stok products exist THEN the Admin_Panel SHALL display the product name and current stock quantity in each alert card
5. WHEN no Kritik_Stok products exist THEN the Admin_Panel SHALL hide the critical stock alerts section

### Requirement 3

**User Story:** As a restoran yöneticisi, I want to see critical stock alerts on the Stock Management page, so that I can prioritize which products to restock while managing inventory.

#### Acceptance Criteria

1. WHEN the Stok_Sekmesi loads THEN the Admin_Panel SHALL display a critical stock alerts section above the stock table
2. WHEN Kritik_Stok products exist THEN the Admin_Panel SHALL display each critical product in a card with a red flashing border animation
3. WHEN Kritik_Stok products exist THEN the Admin_Panel SHALL display the product name and current stock quantity in each alert card
4. WHEN no Kritik_Stok products exist THEN the Admin_Panel SHALL hide the critical stock alerts section on the stock page
5. WHEN stock is updated for a product THEN the Admin_Panel SHALL recalculate and refresh the critical stock alerts immediately

### Requirement 4

**User Story:** As a restoran yöneticisi, I want the open tables section to be positioned above the weekly sales chart on Dashboard, so that I can see both critical information (open tables and stock alerts) at a glance.

#### Acceptance Criteria

1. WHEN the Dashboard loads THEN the Admin_Panel SHALL display the open tables section above the weekly sales chart
2. WHEN the Dashboard loads THEN the Admin_Panel SHALL display the critical stock alerts section above the weekly sales chart
3. WHEN both sections are displayed THEN the Admin_Panel SHALL maintain proper spacing and visual hierarchy between sections
