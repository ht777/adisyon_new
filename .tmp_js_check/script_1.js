
        // --- GLOBAL AYARLAR ---
        const placeholderSvg = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgcnk9IjEwIiBmaWxsPSIjZGVlMzE3Ii8+PHBhdGggZD0iTTUwLDEwTDIwLDIwVjgwTDUwLDkwTDgwLDgwVjIwTDUwLDEwWiIgZmlsbD0iI2YxZjVmOSIgc3Ryb2tlPSIjNjQ3NDhiIiBzdHJva2Utd2lkdGg9IjIiLz48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSIxMCIgZmlsbD0iIzY0NzQ4YiIvPjwvc3ZnPg==';
        let authToken = localStorage.getItem('authToken');
        if(!authToken) window.location.href = '/login.html';
        const getHeaders = () => ({ 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' });
        // fetch override kaldırıldı; tüm çağrılar getHeaders() kullanır
        let chartInstance = null;
        let categories = [];

        // --- YÜKLEME BAR ---
        function showLoading() { document.getElementById('loadingBar').style.width = '100%'; }
        function hideLoading() { setTimeout(() => { document.getElementById('loadingBar').style.width = '0%'; }, 300); }

        // --- SAYFA GEÇİŞLERİ ---
        function showSection(id) {
            document.querySelectorAll('.section').forEach(el => el.classList.add('hidden'));
            const section = document.getElementById(id + 'Section');
            if(section) section.classList.remove('hidden');
            
            const title = document.getElementById('pageTitle');
            if(title) title.innerText = id.charAt(0).toUpperCase() + id.slice(1);

            document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active', 'bg-slate-800'));
            const activeBtn = document.querySelector(`button[onclick="showSection('${id}')"]`);
            if(activeBtn) activeBtn.classList.add('active', 'bg-slate-800');

            // Sayfa yükleme mantığı
            if(id === 'dashboard') loadDashboard();
            else if(id === 'reports') loadReports(); 
            else if(id === 'products') { loadCategories(false); loadProducts(); }
            else if(id === 'categories') loadCategories();
            else if(id === 'tables') loadTables();
            else if(id === 'orders') loadOrders();
            else if(id === 'league') loadLeague();
            else if(id === 'stock') loadStock();
            else if(id === 'waiters') loadWaiters();
            else if(id === 'settings') loadSettings();
        }

        function logout() { localStorage.removeItem('authToken'); window.location.href = '/login.html'; }

        // --- RAPORLAMA FONKSİYONU (DÜZELTİLDİ) ---
        async function loadReports() {
            showLoading();
            const s = document.getElementById('reportStart').value;
            const e = document.getElementById('reportEnd').value;
            
            let url = '/api/admin/reports/overview';
            if(s && e) url += `?start_date=${s}&end_date=${e}`;

            try {
                console.log("Rapor isteniyor:", url);
                const res = await fetch(url, {headers: getHeaders()});
                
                if(!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                
                const data = await res.json();

                // Verileri Doldur
                document.getElementById('repTotalRevenue').innerText = (data.total_revenue || 0).toFixed(2) + ' ₺';
                document.getElementById('repTotalOrders').innerText = data.total_orders || 0;
                document.getElementById('repAvgOrder').innerText = (data.avg_order || 0).toFixed(2) + ' ₺';

                // Ürün tabloları (rapor türü: products veya overview)
                const rt = (document.getElementById('reportType')?.value||'overview');
                if(rt==='products' || rt==='overview'){
                    const ps = await fetch(`/api/admin/reports/products${s&&e?`?start_date=${s}&end_date=${e}`:''}`, {headers: getHeaders()});
                    const pd = await ps.json();
                    const tbody = document.getElementById('topProductsTable');
                    const ptable = document.getElementById('productStatsTable');
                    const arr = (pd.items||[]);
                    tbody.innerHTML = arr.slice(0,10).map(p => `
                            <tr class="hover:bg-gray-50 border-b last:border-0">
                                <td class="p-3 font-medium text-gray-700">${p.name}</td>
                                <td class="p-3 font-bold text-center">${p.qty}</td>
                                <td class="p-3 text-right font-mono text-slate-600">${Number(p.total||0).toFixed(2)} ₺</td>
                            </tr>
                        `).join('');
                    if(ptable) ptable.innerHTML = arr.map(p => `
                            <tr class="hover:bg-gray-50 border-b last:border-0">
                                <td class="p-2 font-medium text-gray-700">${p.name}</td>
                                <td class="p-2 text-right">${p.qty}</td>
                                <td class="p-2 text-right font-mono">${Number(p.total||0).toFixed(2)} ₺</td>
                            </tr>
                        `).join('');
                } else {
                    const tbody = document.getElementById('topProductsTable');
                    const ptable = document.getElementById('productStatsTable');
                    if(tbody) tbody.innerHTML = '';
                    if(ptable) ptable.innerHTML = '';
                }

                // Grafiği Çiz
                if(window.Chart) {
                    const ctx = document.getElementById('reportChart').getContext('2d');
                    if(chartInstance) chartInstance.destroy();
                    
                    // Eğer breakdown verisi boşsa boş grafik çizmemek için kontrol
                    const labels = (data.daily_trend || []).map(x => new Date(x.date).toLocaleDateString('tr-TR'));
                    const values = (data.daily_trend || []).map(x => x.revenue);

                    chartInstance = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Ciro (₺)',
                                data: values,
                                backgroundColor: '#3b82f6',
                                borderRadius: 4
                            }]
                        },
                        options: { responsive: true, maintainAspectRatio: false }
                    });
                }

                if(rt==='cancellations' || rt==='overview'){
                    try{
                        const cs = await fetch(`/api/admin/reports/cancellations${s&&e?`?start_date=${s}&end_date=${e}`:''}`, {headers: getHeaders()});
                        const cd = await cs.json();
                        const ct = document.getElementById('cancellationsTable');
                        const ttl = document.getElementById('cancellationsTotal');
                        if(ct) ct.innerHTML = (cd.items||[]).map(x => `<tr><td class="p-2">#${x.id}</td><td class="p-2">Masa ${x.table_number||'-'} — ${x.table_name||''}</td><td class="p-2 text-right font-mono">${Number(x.total||0).toFixed(2)} ₺</td><td class="p-2 text-sm text-gray-500">${new Date(x.created_at).toLocaleString('tr-TR')}</td></tr>`).join('');
                        if(ttl) ttl.innerText = `${Number(cd.total||0).toFixed(2)} ₺`;
                    }catch(x){}
                } else {
                    const ct = document.getElementById('cancellationsTable');
                    const ttl = document.getElementById('cancellationsTotal');
                    if(ct) ct.innerHTML = '';
                    if(ttl) ttl.innerText = '0.00 ₺';
                }
                try{
                    const ai = await fetch(`/api/admin/reports/insights${s&&e?`?start_date=${s}&end_date=${e}`:''}`, {headers: getHeaders()});
                    const aj = await ai.json();
                    const el = document.getElementById('aiAnalysis');
                    if(el) el.innerText = (aj.analysis||'').toString();
                }catch(x){}
            } catch(e) {
                console.error("Rapor hatası:", e);
                alert("Rapor yüklenirken hata oluştu. Konsolu kontrol edin.");
            } finally {
                hideLoading();
            }
        }
        async function generatePreview(){
            showLoading();
            try{
                const s = document.getElementById('reportStart').value;
                const e = document.getElementById('reportEnd').value;
                let url = '/api/admin/reports/proto';
                if(s && e) url += `?start_date=${s}&end_date=${e}`;
                const r = await fetch(url, {headers: getHeaders()});
                const d = await r.json();
                const box = document.getElementById('reportPreview');
                const name = (d.settings?.restaurant_name)||'Restoran';
                const kpi = d.overview||{};
                const trend = (kpi.daily_trend||[]);
                const prods = (d.products?.items)||[];
                const canc = (d.cancellations?.items)||[];
                box.innerHTML = `
                    <div class="flex items-center gap-3 mb-4">
                        <div class="w-12 h-12 bg-slate-200 rounded"></div>
                        <div>
                            <div class="text-lg font-bold">${name}</div>
                            <div class="text-xs text-gray-500">Önizleme</div>
                        </div>
                    </div>
                    <div class="grid grid-cols-3 gap-3 mb-3">
                        <div class="bg-white p-3 rounded border"><div class="text-xs text-gray-500">Toplam Ciro</div><div class="font-bold">${Number(kpi.total_revenue||0).toFixed(2)} ₺</div></div>
                        <div class="bg-white p-3 rounded border"><div class="text-xs text-gray-500">Toplam Sipariş</div><div class="font-bold">${kpi.total_orders||0}</div></div>
                        <div class="bg-white p-3 rounded border"><div class="text-xs text-gray-500">İptaller</div><div class="font-bold">${kpi.cancelled_orders||0}</div></div>
                    </div>
                    <div class="bg-white p-3 rounded border mb-3">
                        <div class="font-bold mb-2">Top Ürünler</div>
                        ${prods.slice(0,5).map(p=>`<div class='flex justify-between text-sm'><span>${p.name}</span><span class='font-mono'>${Number(p.total||0).toFixed(2)} ₺</span></div>`).join('')||'<div class="text-gray-400 text-sm">Veri yok</div>'}
                    </div>
                    <div class="bg-white p-3 rounded border">
                        <div class="font-bold mb-2">İptaller</div>
                        ${canc.slice(0,5).map(x=>`<div class='flex justify-between text-sm'><span>Masa ${x.table_number||'-'} — ${x.table_name||''}</span><span class='font-mono'>${Number(x.total||0).toFixed(2)} ₺</span></div>`).join('')||'<div class="text-gray-400 text-sm">Veri yok</div>'}
                    </div>
                `;
            }catch(x){ alert('Önizleme oluşturulamadı'); }
            finally{ hideLoading(); }
        }
        function presetRange(type){
            const s = document.getElementById('reportStart');
            const e = document.getElementById('reportEnd');
            const now = new Date();
            const fmt = d => d.toISOString().slice(0,10);
            if(type==='today'){
                const d = fmt(now);
                s.value = d; e.value = d;
            }else if(type==='yesterday'){
                const y = new Date(now.getTime()-86400000);
                const d = fmt(y);
                s.value = d; e.value = d;
            }else{
                const days = parseInt(type);
                const start = new Date(now.getTime()-days*86400000);
                s.value = fmt(start); e.value = fmt(now);
            }
            loadReports();
        }
        async function exportReport(fmt){
            showLoading();
            try{
                const s = document.getElementById('reportStart').value;
                const e = document.getElementById('reportEnd').value;
                let url = `/api/admin/reports/export?format=${fmt}`;
                if(s && e) url += `&start_date=${s}&end_date=${e}`;
                const r = await fetch(url, {headers: getHeaders()});
                if(fmt==='pdf' && r.ok){
                    const url = '/static/uploads/closing_report.pdf?t=' + new Date().getTime();
                    const a = document.createElement('a'); a.href=url; a.download='closing_report.pdf'; a.click();
                } else if(fmt==='csv' && r.ok){
                    const url = '/static/uploads/report_export.csv?t=' + new Date().getTime();
                    const a = document.createElement('a'); a.href=url; a.download='report_export.csv'; a.click();
                } else {
                    alert('Dışa aktarma başarısız');
                }
            }catch(x){ alert('İstek hatası'); }
            finally{ hideLoading(); }
        }

        async function loadProductMatrix(){
            showLoading();
            try{
                const res = await fetch('/api/admin/reports/product-matrix', {headers: getHeaders()});
                const data = await res.json();
                const ai = document.getElementById('aiAnalysis');
                ai.innerText = (data.analysis || '').toString();
            }catch(e){ alert('Ürün matrisi getirilemedi'); }
            finally{ hideLoading(); }
        }

        async function downloadClosingPdf(){
            try{
                const res = await fetch('/api/admin/reports/closing-report-pdf', {headers: getHeaders()});
                if(res.ok){
                    const url = '/static/uploads/closing_report.pdf?t=' + new Date().getTime();
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'closing_report.pdf';
                    a.click();
                } else {
                    alert('PDF oluşturulamadı');
                }
            }catch(e){ alert('PDF isteği başarısız'); }
        }
        async function downloadFullPdf(){
            showLoading();
            try{
                const s = document.getElementById('reportStart').value;
                const e = document.getElementById('reportEnd').value;
                let url = '/api/admin/reports/full-pdf';
                const qs = [];
                if(s && e){ qs.push(`start_date=${s}`); qs.push(`end_date=${e}`); }
                qs.push('include_ai=true');
                if(qs.length) url += '?' + qs.join('&');
                const res = await fetch(url, {headers: getHeaders()});
                if(res.ok){
                    const fname = `full_report_${s||''}_${e||''}.pdf`;
                    const a = document.createElement('a');
                    a.href = `/static/uploads/${fname}`;
                    a.download = fname;
                    a.click();
                } else { alert('PDF oluşturulamadı'); }
            }catch(x){ alert('İstek hatası'); }
            finally{ hideLoading(); }
        }
        async function loadReportArchive(){
            showLoading();
            try{
                const r = await fetch('/api/admin/reports/archive', {headers: getHeaders()});
                const d = await r.json();
                const box = document.getElementById('reportArchive');
                box.classList.remove('hidden');
                const rows = (d.files||[]).map(f=>`<tr class="border-b"><td class="p-2"><a href="${f.url}" class="text-blue-600 hover:underline" download>${f.name}</a></td><td class="p-2">${f.type||''}</td><td class="p-2 text-right">${(f.size||0)} B</td><td class="p-2 text-sm text-gray-500">${(f.modified||'').toString()}</td><td class="p-2 text-right"><button onclick="deleteReportFile('${f.name}')" class="px-2 py-1 bg-red-600 text-white rounded text-xs">Sil</button></td></tr>`).join('');
                box.innerHTML = rows ? (`<table class="w-full text-sm"><thead class="bg-gray-50 text-gray-500"><tr><th class="p-2 text-left">Dosya</th><th class="p-2">Tür</th><th class="p-2 text-right">Boyut</th><th class="p-2">Güncellendi</th><th class="p-2 text-right">İşlem</th></tr></thead><tbody>${rows}</tbody></table>`) : '<div class="text-gray-400">Arşiv boş</div>';
            }catch(x){}
            finally{ hideLoading(); }
        }
        function clearReportArchive(){
            const box = document.getElementById('reportArchive');
            box.classList.add('hidden');
            box.innerHTML = '';
        }
        async function deleteReportFile(name){
            showLoading();
            try{
                const r = await fetch('/api/admin/reports/archive/' + encodeURIComponent(name), {method:'DELETE', headers: getHeaders()});
                if(r.ok){ loadReportArchive(); }
                else{ alert('Silme başarısız'); }
            }catch(x){ alert('İstek hatası'); }
            finally{ hideLoading(); }
        }
        

        async function loadLeague(){
            showLoading();
            try{
                const usersRes = await fetch('/api/auth/users', {headers: getHeaders()});
                const users = await usersRes.json();
                const tbody = document.getElementById('leagueTable');
                const rows = (users || []).map(u => {
                    return `<tr><td class="p-3 font-medium text-gray-800">${u.username}</td><td class="p-3 text-right font-mono">-</td><td class="p-3 text-right font-mono">-</td></tr>`;
                }).join('');
                tbody.innerHTML = rows;
            }catch(e){}finally{hideLoading();}
        }

        async function loadWaiters(){
            showLoading();
            try{
                const r = await fetch('/api/waiters', {headers: getHeaders()});
                const d = await r.json();
                const tbody = document.getElementById('waitersTable');
                const rows = (d||[]).map(w=>{
                    return `<tr class="border-b hover:bg-gray-50"><td class="p-4 font-medium">${w.full_name||'-'}</td><td class="p-4">${w.username}</td><td class="p-4"><input id="assign-${w.id}" class="border p-2 rounded w-64" placeholder="Masa numaraları (virgül)"></td><td class="p-4 text-center"><button onclick="assignTables(${w.id})" class="bg-slate-800 text-white px-3 py-1 rounded mr-2">Ata</button><button onclick="resetWaiterPin(${w.id})" class="bg-amber-600 text-white px-3 py-1 rounded mr-2">PIN Sıfırla</button><button onclick="deleteWaiter(${w.id})" class="bg-red-600 text-white px-3 py-1 rounded">Sil</button></td></tr>`;
                }).join('');
                tbody.innerHTML = rows || '<tr><td colspan="4" class="p-4 text-center text-gray-400">Garson yok</td></tr>';
            }catch(x){}
            finally{ hideLoading(); }
        }
        async function addWaiter(){
            const n = document.getElementById('newWaiterName').value.trim();
            if(!n){ alert('Ad Soyad gerekli'); return; }
            showLoading();
            try{
                const r = await fetch('/api/waiters', {method:'POST', headers:getHeaders(), body: JSON.stringify({full_name:n})});
                if(r.ok){ const d=await r.json(); alert(`Garson eklendi. Şifre: ${d.pin}`); document.getElementById('newWaiterName').value=''; loadWaiters(); }
                else{ alert('Ekleme başarısız'); }
            }catch(x){ alert('İstek hatası'); }
            finally{ hideLoading(); }
        }
        async function assignTables(id){
            showLoading();
            try{
                const raw = document.getElementById('assign-'+id).value||'';
                const nums = raw.split(',').map(x=>parseInt(x.trim())).filter(x=>!isNaN(x));
                const t = await fetch('/api/tables?active_only=false', {headers:getHeaders()});
                const d = await t.json();
                const ids = d.filter(x=>nums.includes(x.number)).map(x=>x.id);
                await fetch('/api/waiters/'+id+'/tables', {method:'PUT', headers:getHeaders(), body: JSON.stringify({table_ids: ids})});
                alert('Atandı');
            }catch(x){ alert('Atama hatası'); }
            finally{ hideLoading(); }
        }
        async function deleteWaiter(id){
            if(!confirm('Silinsin?')) return;
            showLoading();
            try{ await fetch('/api/waiters/'+id, {method:'DELETE', headers:getHeaders()}); loadWaiters(); }
            catch(x){}
            finally{ hideLoading(); }
        }
        async function resetWaiterPin(id){
            showLoading();
            try{ const r=await fetch('/api/waiters/'+id+'/reset-pin', {method:'POST', headers:getHeaders()}); if(r.ok){ const d=await r.json(); alert('Yeni PIN: '+d.pin); } else { alert('PIN sıfırlama başarısız'); } }
            catch(x){ alert('İstek hatası'); }
            finally{ hideLoading(); }
        }

        async function loadStock(){
            showLoading();
            try{
                const res = await fetch('/api/products', {headers: getHeaders()});
                const data = await res.json();
                const tbody = document.getElementById('stockTable');
                tbody.innerHTML = (data||[]).map(p => `
                    <tr class="border-b hover:bg-gray-50 transition">
                        <td class="p-4 font-medium text-gray-800">${p.name}</td>
                        <td class="p-4 text-right font-mono">${p.track_stock ? p.stock : '∞'}</td>
                        <td class="p-4 text-right">${p.track_stock ? ('<input type="number" min="0" class="w-24 border p-2 rounded-lg text-right" id="stock-' + p.id + '" value="' + p.stock + '">') : '<span class="text-xs text-gray-400">Takip Kapalı</span>'}</td>
                        <td class="p-4 text-center"><button onclick="${p.track_stock ? ('saveStock(' + p.id + ')') : ('toggleTrack(' + p.id + ', true)')}" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">${p.track_stock ? 'Güncelle' : 'Takibi Aç'}</button></td>
                    </tr>
                `).join('');
            }catch(e){}finally{hideLoading();}
        }

        async function saveStock(productId){
            showLoading();
            try{
                const input = document.getElementById('stock-' + productId);
                const qty = parseInt(input.value||'0');
                const res = await fetch('/api/products/' + productId, {method:'PUT', headers: getHeaders(), body: JSON.stringify({stock: qty})});
                if(res.ok){ loadStock(); }
                else{ alert('Güncelleme başarısız'); }
            }catch(e){ alert('İstek hatası'); }finally{ hideLoading(); }
        }

        async function toggleTrack(id, status){
            showLoading();
            try{
                await fetch('/api/products/' + id, {method:'PUT', headers: getHeaders(), body: JSON.stringify({track_stock: status, stock: status ? 0 : 0})});
                loadStock();
            }catch(e){}finally{hideLoading();}
        }

        // --- DASHBOARD ---
        async function loadDashboard() {
            showLoading();
            try {
                const res = await fetch('/api/admin/dashboard', {headers: getHeaders()});
                if(res.status === 401) { logout(); return; }
                const data = await res.json();
                
                document.getElementById('statProducts').innerText = data.overview.total_products || '0';
                document.getElementById('statRevenue').innerText = (data.sales.today_revenue || 0).toFixed(2) + ' ₺';
                document.getElementById('statTodayOrders').innerText = data.sales.today_orders || '0';
                document.getElementById('statActiveOrders').innerText = data.sales.active_orders || '0';
                
                if(window.Chart) {
                    const ctx = document.getElementById('salesChart').getContext('2d');
                    if(chartInstance) chartInstance.destroy();
                    chartInstance = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: (data.sales.daily_trend || []).map(d => new Date(d.date).toLocaleDateString('tr-TR', {day:'numeric', month:'short'})),
                            datasets: [{
                                label: 'Günlük Ciro',
                                data: (data.sales.daily_trend || []).map(d => d.revenue),
                                borderColor: '#10b981',
                                tension: 0.3,
                                fill: true,
                                backgroundColor: 'rgba(16, 185, 129, 0.1)'
                            }]
                        },
                        options: { responsive: true, maintainAspectRatio: false }
                    });
                }
                try{
                    const pr = await fetch('/api/products', {headers:getHeaders()});
                    const pd = await pr.json();
                    const low = (pd||[]).filter(p => p.track_stock && (p.stock||0) <= 15);
                    const ls = document.getElementById('lowStockList');
                    if(ls) ls.innerHTML = low.length ? low.map(p=>`<div class="flex items-center gap-2 text-sm"><span class="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span><span class="font-bold">${p.name}</span><span class="font-mono">(${p.stock})</span></div>`).join('') : '<div class="text-gray-400 text-sm">Uyarı yok</div>';
                }catch(x){}
                try{
                    const tr = await fetch('/api/tables/open', {headers:getHeaders()});
                    const td = await tr.json();
                    const grid = document.getElementById('openTablesGrid');
                    if(grid) {
                        const items = (td||[]).map(t=>`<div class="border rounded-xl p-4 cursor-pointer ${t.total_amount>0?'border-green-300 bg-green-50':'border-gray-200 bg-white'}" onclick="openTableActions(${t.table_id}, ${t.table_number})"><div class="flex justify-between items-center"><div class="font-bold">masa - ${t.table_number}</div><div class="font-mono">${(t.total_amount||0).toFixed(2)} ₺</div></div><div class="mt-2 text-xs text-gray-600">${t.items.length} kalem</div></div>`).join('');
                        grid.innerHTML = items || '<div class="text-gray-400 text-sm">Hiç açık masa yok</div>';
                    }
                try{
                    const sr = await fetch('/api/tables/stats/summary', {headers:getHeaders()});
                    const sd = await sr.json();
                    const stats = document.getElementById('tableStats');
                    if(stats) stats.innerHTML = `
                        <div class="bg-gray-50 rounded-lg p-3 text-center"><div class="text-xs text-gray-500">Toplam Aktif Masa</div><div class="text-xl font-bold">${sd.total_tables||0}</div></div>
                        <div class="bg-gray-50 rounded-lg p-3 text-center"><div class="text-xs text-gray-500">Aktif (Son 2 saat)</div><div class="text-xl font-bold">${sd.active_tables||0}</div></div>
                        <div class="bg-gray-50 rounded-lg p-3 text-center"><div class="text-xs text-gray-500">Müsait</div><div class="text-xl font-bold">${sd.available_tables||0}</div></div>
                    `;
                }catch(x){}
                }catch(x){}
            } catch(e){} finally { hideLoading(); }
        }
        async function closeTable(id){ showLoading(); try{ await fetch(`/api/tables/close/${id}`, {method:'POST', headers:getHeaders()}); loadDashboard(); }catch(x){} finally{ hideLoading(); } }

        // Açık masalar modalı
        let actionTableId=null; let actionTableNum=null;
        function openTableActions(id, num){ actionTableId=id; actionTableNum=num; const m=document.getElementById('tableActionsModalAdmin'); document.getElementById('tamTitleAdmin').innerText=`Masa ${num}`; m.classList.remove('hidden'); m.classList.add('flex'); }
        function closeTableActions(){ const m=document.getElementById('tableActionsModalAdmin'); m.classList.add('hidden'); m.classList.remove('flex'); }
        async function adminActionDetails(){ await openTableDetails(actionTableId); }
        async function adminActionClose(){ await closeTable(actionTableId); closeTableActions(); }
        async function adminActionPrint(){ await printBill(actionTableId); }
        async function adminActionTransfer(){ const tgt=prompt('Hedef masa numarası:'); if(!tgt) return; showLoading(); try{ const r=await fetch('/api/tables?active_only=false',{headers:getHeaders()}); const d=await r.json(); const t=d.find(x=>x.number==parseInt(tgt)); if(!t){ alert('Masa bulunamadı'); } else { await fetch(`/api/tables/transfer/${actionTableId}/${t.id}`,{method:'POST',headers:getHeaders()}); } }catch(x){} finally{ hideLoading(); closeTableActions(); loadDashboard(); }
        async function adminActionMerge(){ const tgt=prompt('Birleştirilecek masa numarası:'); if(!tgt) return; showLoading(); try{ const r=await fetch('/api/tables?active_only=false',{headers:getHeaders()}); const d=await r.json(); const t=d.find(x=>x.number==parseInt(tgt)); if(!t){ alert('Masa bulunamadı'); } else { await fetch(`/api/tables/merge/${actionTableId}/${t.id}`,{method:'POST',headers:getHeaders()}); } }catch(x){} finally{ hideLoading(); closeTableActions(); loadDashboard(); }
        async function adminActionCancel(){ showLoading(); try{ const dr=await fetch(`/api/tables/details/${actionTableId}`,{headers:getHeaders()}); const d=await dr.json(); const active=(d.orders||[]).filter(o=>['pending','preparing','bekliyor','hazirlaniyor'].includes((o.status||'').toLowerCase())); for(const o of active){ await fetch(`/api/orders/${o.id}/status`,{method:'PUT',headers:getHeaders(),body:JSON.stringify({status:'cancelled'})}); } }catch(x){} finally{ hideLoading(); closeTableActions(); loadDashboard(); }

        // --- DİĞER FONKSİYONLAR ---
        async function loadProducts() {
            showLoading();
            try {
                const res = await fetch('/api/products', {headers: getHeaders()}); 
                const rawData = await res.json();
                const products = Array.isArray(rawData) ? rawData : (rawData.products || []);
                
                document.getElementById('productsTable').innerHTML = products.map(p => {
                    const imgUrl = (p.image_url && p.image_url.length > 5) ? p.image_url : placeholderSvg;
                    const catName = p.category ? p.category.name : (categories.find(c => c.id == p.category_id)?.name || '-');
                    return `
                    <tr class="border-b hover:bg-gray-50 transition">
                        <td class="p-4"><div class="w-12 h-12 rounded-lg overflow-hidden bg-gray-100 border"><img src="${imgUrl}" class="w-full h-full object-cover" onerror="this.src='${placeholderSvg}'"></div></td>
                        <td class="p-4 font-medium text-gray-800">${p.name}</td>
                        <td class="p-4 text-sm text-gray-500">${catName}</td>
                        <td class="p-4 font-bold text-green-600 font-mono">${p.price.toFixed(2)} ₺</td>
                        <td class="p-4 text-center"><button onclick="deleteProduct(${p.id})" class="text-red-500 hover:bg-red-50 p-2 rounded-full transition"><i class="fas fa-trash"></i></button></td>
                    </tr>`;
                }).join('');
            } catch(e){} finally { hideLoading(); }
        }
        // (Diğer fonksiyonlar ürün ekleme/silme vb. aynı mantıkla buraya eklenebilir, yer kaplamaması için kısalttım)
        
        async function saveProduct(e){
            e.preventDefault();
            showLoading();
            const fd=new FormData(e.target);
            const d={
                name:fd.get('name'),
                description:fd.get('description'),
                price:parseFloat(fd.get('price')),
                category_id:parseInt(fd.get('category_id')),
                is_active:true,
                track_stock: !!document.getElementById('track_stock')?.checked,
                stock: parseInt(document.getElementById('stock_input')?.value||'0')
            };
            try{
                const r=await fetch('/api/products',{method:'POST',headers:getHeaders(),body:JSON.stringify(d)});
                if(r.ok){
                    const np=await r.json();
                    const im=document.getElementById('productImage').files[0];
                    if(im){
                        const f=new FormData();
                        f.append('file',im);
                        await fetch(`/api/products/${np.id}/image`,{method:'POST',headers:{'Authorization':`Bearer ${authToken}`},body:f});
                    }
                    closeProductModal();
                    loadProducts();
                    if(document.getElementById('stockSection') && !document.getElementById('stockSection').classList.contains('hidden')){ loadStock(); }
                    alert('Eklendi!');
                } else {
                    alert('Hata');
                }
            }catch(err){ alert(err); }
            finally{ hideLoading(); }
        }
        async function deleteProduct(id){if(confirm('Sil?')){showLoading();await fetch(`/api/products/${id}`,{method:'DELETE',headers:getHeaders()});loadProducts();hideLoading();}}
        async function openProductModal(){const r=await fetch('/api/products/categories', {headers: getHeaders()});const d=await r.json();categories=d.categories||d;document.getElementById('categorySelect').innerHTML='<option>Seç</option>'+categories.map(c=>`<option value="${c.id}">${c.name}</option>`);document.getElementById('productModal').classList.remove('hidden');}
        function closeProductModal(){document.getElementById('productModal').classList.add('hidden');}
        
        // Kategoriler
        async function loadCategories(render=true){if(render)showLoading();try{const r=await fetch('/api/products/categories', {headers: getHeaders()});const d=await r.json();categories=d.categories||d;if(render)document.getElementById('categoriesTable').innerHTML=categories.map(c=>`<tr class="border-b hover:bg-gray-50"><td class="p-4 text-2xl">${c.icon||''}</td><td class="p-4 font-bold text-gray-700">${c.name}</td><td class="p-4 text-center"><button onclick="deleteCategory(${c.id})" class="text-red-500 hover:bg-red-50 p-2 rounded-full"><i class="fas fa-trash"></i></button></td></tr>`).join('');}catch(e){}finally{if(render)hideLoading();}}
        async function addCategory(){const n=prompt('Ad:');if(!n)return;const i=prompt('İkon:','🍔');showLoading();await fetch('/api/products/categories',{method:'POST',headers:getHeaders(),body:JSON.stringify({name:n,icon:i})});loadCategories();hideLoading();}
        async function deleteCategory(id){if(confirm('Sil?')){showLoading();await fetch(`/api/products/categories/${id}`,{method:'DELETE',headers:getHeaders()});loadCategories();hideLoading();}}

        // Masalar
        async function loadTables(){
            showLoading();
            try{
                const r=await fetch('/api/tables',{headers:getHeaders()});
                const d=await r.json();
                const tbody=document.getElementById('tablesTable');
                if(tbody) {
                    const rows = d.map(t=>`<tr class="border-b hover:bg-gray-50"><td class="p-4 font-medium">${t.name}</td><td class="p-4 font-bold text-blue-600">${t.number}</td><td class="p-4 text-center"><button onclick="showQR(${t.id})" class="text-blue-600 mr-3 font-bold text-sm">QR</button><button onclick="deleteTable(${t.id})" class="text-red-500"><i class="fas fa-trash"></i></button></td></tr>`).join('');
                    tbody.innerHTML = rows || '<tr><td colspan="3" class="p-4 text-center text-gray-400">Hiç aktif masa yok</td></tr>';
                }
                try{
                    const or=await fetch('/api/tables/open',{headers:getHeaders()});
                    const od=await or.json();
                    const grid=document.getElementById('openTablesGridTables');
                    if(grid) {
                        const items=(od||[]).map(t=>`<div class="border rounded-xl p-4 cursor-pointer ${t.total_amount>0?'border-green-300 bg-green-50':'border-gray-200 bg-white'}" onclick="openTableActions(${t.table_id}, ${t.table_number})"><div class="flex justify-between items-center"><div class="font-bold">masa - ${t.table_number}</div><div class="font-mono">${(t.total_amount||0).toFixed(2)} ₺</div></div><div class="mt-2 text-xs text-gray-600">${t.items.length} kalem</div></div>`).join('');
                        grid.innerHTML = items || '<div class="text-gray-400 text-sm">Hiç açık masa yok</div>';
                    }
                }catch(x){}
            }catch(e){}
            finally{hideLoading();}
        }
        async function openTableDetails(id){
            showLoading();
            try{
                const r=await fetch(`/api/tables/details/${id}`, {headers:getHeaders()});
                const d=await r.json();
                const w=window.open("","_blank");
                const doc=w.document;
                const wrap=doc.createElement('div');
                wrap.className='p-6';
                const container=doc.createElement('div');
                container.className='max-w-2xl mx-auto';
                const head=doc.createElement('div');
                head.className='flex justify-between items-center mb-4';
                const h2=doc.createElement('h2'); h2.className='text-2xl font-bold'; h2.textContent=`Masa ${d.table_number}`;
                const ts=doc.createElement('span'); ts.className='text-sm text-gray-500'; ts.textContent=d.arrival_time?new Date(d.arrival_time).toLocaleString('tr-TR'):'';
                head.appendChild(h2); head.appendChild(ts);
                const totalCard=doc.createElement('div'); totalCard.className='bg-white border rounded-xl p-4 mb-4';
                const totalRow=doc.createElement('div'); totalRow.className='flex justify-between';
                const totalLbl=doc.createElement('div'); totalLbl.className='font-bold'; totalLbl.textContent='Toplam';
                const totalVal=doc.createElement('div'); totalVal.className='font-mono text-lg'; totalVal.textContent=`${(d.total_amount||0).toFixed(2)} ₺`;
                totalRow.appendChild(totalLbl); totalRow.appendChild(totalVal); totalCard.appendChild(totalRow);
                const ordersBox=doc.createElement('div'); ordersBox.className='bg-white border rounded-xl p-4';
                const ordersTitle=doc.createElement('h3'); ordersTitle.className='font-bold mb-2'; ordersTitle.textContent='Siparişler'; ordersBox.appendChild(ordersTitle);
                (d.orders||[]).forEach(o=>{
                    const sec=doc.createElement('div'); sec.className='border-b py-2';
                    const top=doc.createElement('div'); top.className='flex justify-between';
                    const left=doc.createElement('div'); left.className='font-semibold'; left.textContent=`#${o.id} - ${o.status}`;
                    const right=doc.createElement('div'); right.className='text-xs text-gray-500'; right.textContent=new Date(o.created_at).toLocaleString('tr-TR');
                    top.appendChild(left); top.appendChild(right); sec.appendChild(top);
                    if(o.customer_notes){ const notes=doc.createElement('div'); notes.className='text-xs text-gray-600'; notes.textContent=`Not: ${o.customer_notes}`; sec.appendChild(notes); }
                    const table=doc.createElement('table'); table.className='w-full text-sm mt-2';
                    const thead=doc.createElement('thead'); thead.className='text-gray-500';
                    thead.innerHTML='<tr><th class="text-left">Ürün</th><th class="text-center">Adet</th><th class="text-right">Fiyat</th><th class="text-right">Tutar</th></tr>';
                    const tbody=doc.createElement('tbody');
                    (o.items||[]).forEach(it=>{
                        const tr=doc.createElement('tr');
                        tr.innerHTML=`<td>${it.name}</td><td class="text-center">${it.quantity}</td><td class="text-right font-mono">${Number(it.unit_price||0).toFixed(2)} ₺</td><td class="text-right font-mono">${Number(it.subtotal||0).toFixed(2)} ₺</td>`;
                        tbody.appendChild(tr);
                    });
                    table.appendChild(thead); table.appendChild(tbody); sec.appendChild(table);
                    ordersBox.appendChild(sec);
                });
                const actions=doc.createElement('div'); actions.className='mt-4 text-right';
                const btn=doc.createElement('button'); btn.className='px-4 py-2 bg-slate-800 text-white rounded hover:bg-slate-900'; btn.textContent='Yazdır'; btn.onclick=()=>{window.opener && window.opener.printBill(id); w.close();};
                actions.appendChild(btn); ordersBox.appendChild(actions);
                container.appendChild(head); container.appendChild(totalCard); container.appendChild(ordersBox);
                wrap.appendChild(container); doc.body.appendChild(wrap);
            }catch(x){ alert('Detay yüklenemedi'); }
            finally{ hideLoading(); }
        }
        async function printBill(id){
            showLoading();
            try{ await fetch(`/api/tables/print-bill/${id}`, {method:'POST', headers:getHeaders()}); showToast('Hesap yazdırılıyor', 'blue'); }
            catch(x){ alert('Yazdırma başarısız'); }
            finally{ hideLoading(); }
        }
        async function addTableQuick(){
            const n=document.getElementById('quickTableName')?.value.trim();
            const num=parseInt(document.getElementById('quickTableNumber')?.value||'0');
            if(!n || !num){ alert('Masa adı ve numarası gerekli'); return; }
            showLoading();
            try{ await fetch('/api/tables',{method:'POST',headers:getHeaders(),body:JSON.stringify({name:n,number:num})}); document.getElementById('quickTableName').value=''; document.getElementById('quickTableNumber').value=''; loadTables(); }
            catch(x){ alert('Ekleme hatası'); }
            finally{ hideLoading(); }
        }
        async function addTable(){const n=prompt('Ad:');if(!n)return;const num=prompt('No:');showLoading();await fetch('/api/tables',{method:'POST',headers:getHeaders(),body:JSON.stringify({name:n,number:parseInt(num)})});loadTables();hideLoading();}
        async function deleteTable(id){if(confirm('Sil?')){showLoading();await fetch(`/api/tables/${id}`,{method:'DELETE',headers:getHeaders()});loadTables();hideLoading();}}
        async function reactivateTableByNumber(){
            const num=parseInt(document.getElementById('reactivateTableNumber')?.value||'0');
            if(!num){ alert('Masa no gerekli'); return; }
            showLoading();
            try{
                const r=await fetch('/api/tables?active_only=false',{headers:getHeaders()});
                const d=await r.json();
                const t=(d||[]).find(x=>x.number===num);
                if(!t){ alert('Masa bulunamadı'); return; }
                if(t.is_active){ alert('Masa zaten aktif'); return; }
                const u=await fetch(`/api/tables/${t.id}`,{method:'PUT',headers:getHeaders(),body:JSON.stringify({is_active:true})});
                if(u.ok){ document.getElementById('reactivateTableNumber').value=''; loadTables(); }
                else{ alert('Aktifleştirme başarısız'); }
            }catch(e){ alert('İstek hatası'); }
            finally{ hideLoading(); }
        }
        async function showQR(id){
            const r=await fetch(`/api/tables/${id}/qr`,{headers:getHeaders()});
            const d=await r.json();
            const w=window.open("","_blank");
            const doc=w.document;
            const root=doc.createElement('div');
            root.style.textAlign='center';
            root.style.marginTop='50px';
            root.style.fontFamily='sans-serif';
            const h1=doc.createElement('h1');
            h1.textContent=d.table_name||`Masa ${id}`;
            const img=doc.createElement('img');
            img.width=300;
            img.src=d.qr_url||'';
            const br=doc.createElement('br');
            const btn=doc.createElement('button');
            btn.textContent='YAZDIR';
            btn.style.marginTop='20px';
            btn.style.padding='10px 20px';
            btn.style.fontSize='1.2em';
            btn.onclick=()=>w.print();
            root.appendChild(h1);root.appendChild(img);root.appendChild(br);root.appendChild(btn);
            doc.body.appendChild(root);
        }

        // Siparişler
        async function loadOrders(){showLoading();try{const r=await fetch('/api/orders',{headers:getHeaders()});const d=await r.json();document.getElementById('ordersTable').innerHTML=d.map(o=>`<tr class="border-b hover:bg-gray-50"><td class="p-4 text-gray-500 font-mono">#${o.id}</td><td class="p-4 font-bold">${o.table_name}</td><td class="p-4 font-bold text-slate-700">${o.total_amount.toFixed(2)} ₺</td><td class="p-4"><span class="bg-gray-100 px-2 py-1 rounded text-xs font-bold text-gray-600 uppercase">${o.status}</span></td><td class="p-4 text-sm text-gray-500">${new Date(o.created_at).toLocaleTimeString('tr-TR').slice(0,5)}</td><td class="p-4 text-center"><button onclick="cancelOrder(${o.id})" class="text-red-500 border border-red-200 px-2 py-1 rounded text-xs hover:bg-red-50">İptal</button></td></tr>`).join('');}catch(e){}finally{hideLoading();}}
        async function cancelOrder(id){if(!confirm('İptal?'))return;showLoading();await fetch(`/api/orders/${id}/status`,{method:'PUT',headers:getHeaders(),body:JSON.stringify({status:'cancelled'})});loadOrders();hideLoading();}

        // Ayarlar ve Logo
        function handleLogoSelect(input){if(input.files&&input.files[0]){const r=new FileReader();r.onload=e=>{document.getElementById('currentLogo').src=e.target.result;document.getElementById('currentLogo').style.display='block';document.getElementById('logoPlaceholder').style.display='none';document.getElementById('uploadBtn').classList.remove('hidden');};r.readAsDataURL(input.files[0]);document.getElementById('fileNameDisplay').innerText=input.files[0].name;}}
        async function uploadLogo(){const fi=document.getElementById('logoInput');if(fi.files.length===0)return;showLoading();const fd=new FormData();fd.append('file',fi.files[0]);try{const r=await fetch('/api/admin/settings/logo',{method:'POST',headers:{'Authorization':`Bearer ${authToken}`},body:fd});if(r.ok){alert('Yüklendi!');loadSettings();}else alert('Hata');}catch(e){alert(e);}finally{hideLoading();}}
        async function loadSettings(){showLoading();try{const r=await fetch('/api/admin/settings',{headers:getHeaders()});if(r.ok){const d=await r.json();document.getElementById('setRestName').value=d.restaurant_name||'';document.getElementById('setCurrency').value=d.currency||'';document.getElementById('setTax').value=d.tax_rate||0;document.getElementById('setService').value=d.service_charge||0;document.getElementById('setTimeout').value=d.order_timeout_minutes||30;document.getElementById('setWifi').value=d.wifi_password||'';if(d.logo_url){const url=d.logo_url+'?t='+new Date().getTime();document.getElementById('currentLogo').src=url;document.getElementById('currentLogo').style.display='block';document.getElementById('logoPlaceholder').style.display='none';const al=document.getElementById('adminPanelLogo');if(al){al.src=url;al.style.display='block';al.classList.remove('hidden');}}}}catch(e){}finally{hideLoading();}}
        async function saveSettings(e){e.preventDefault();showLoading();const d={restaurant_name:document.getElementById('setRestName').value,currency:document.getElementById('setCurrency').value,tax_rate:parseFloat(document.getElementById('setTax').value),service_charge:parseFloat(document.getElementById('setService').value),order_timeout_minutes:parseInt(document.getElementById('setTimeout').value),wifi_password:document.getElementById('setWifi').value};await fetch('/api/admin/settings',{method:'PUT',headers:getHeaders(),body:JSON.stringify(d)});alert('Kaydedildi!');hideLoading();}

        // WebSocket
        function connectWS() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            ws.onopen = () => ws.send(JSON.stringify({type:'register', client_type:'admin'}));
            ws.onmessage = (e) => {
                const raw = typeof e.data === 'string' ? e.data.trim() : '';
                if(!raw) return;
                let m;
                try { m = JSON.parse(raw); } catch(_) { return; }
                if(m.type === 'waiter_call' || m.type === 'bill_request') {
                    document.getElementById('bellSound').play().catch(()=>{});
                    showToast(m.message, m.type === 'bill_request' ? 'purple' : 'orange');
                } else if(m.type === 'stock_warning') {
                    showToast(m.message, 'red');
                } else if(m.type && m.type.includes('order')) {
                    if(!document.getElementById('dashboardSection').classList.contains('hidden')) loadDashboard();
                    if(!document.getElementById('ordersSection').classList.contains('hidden')) loadOrders();
                    if(!document.getElementById('tablesSection').classList.contains('hidden')) loadTables();
                } else if(m.type === 'table_status') {
                    showToast(`${m.table_name} aktif oldu`, 'blue');
                    if(!document.getElementById('dashboardSection').classList.contains('hidden')) loadDashboard();
                    if(!document.getElementById('tablesSection').classList.contains('hidden')) loadTables();
                }
            };
            ws.onclose = () => setTimeout(connectWS, 3000);
        }

        function showToast(msg, color) {
            const div = document.createElement('div');
            div.className = `fixed top-5 right-5 bg-white border-l-4 border-${color}-500 text-gray-700 px-6 py-4 shadow-2xl z-50 flex items-center gap-3 rounded-r toast-notification`;
            div.innerHTML = `<i class="fas fa-bell text-${color}-500 text-xl"></i> <span class="font-bold">${msg}</span>`;
            document.body.appendChild(div);
            setTimeout(() => div.remove(), 5000);
        }

        let __appInitDone = false;
        function initApp(){
            if(__appInitDone) return;
            __appInitDone = true;
            showSection('dashboard');
            loadSettings();
            connectWS();
        }
        // BAŞLAT
        window.onload = async () => {
            if(!authToken){ window.location.href = '/login.html'; return; }
            try{
                const r = await fetch('/api/auth/me');
                if(r.ok){
                    const me = await r.json();
                    const rv = typeof me.role === 'string' ? me.role.toLowerCase() : (me.role && me.role.toString ? me.role.toString().toLowerCase() : '');
                    if(rv !== 'admin' && rv !== 'supervisor'){
                        alert('Yönetim paneli için yetkiniz yok.');
                        logout();
                        return;
                    }
                }
            }catch(e){}
            initApp();
        };
        document.addEventListener('DOMContentLoaded', ()=>{ if(!__appInitDone) initApp(); });
        document.addEventListener('readystatechange', ()=>{ if(document.readyState==='complete' && !__appInitDone) initApp(); });
        setTimeout(()=>{ if(!__appInitDone) initApp(); }, 1500);
        function filterStockTable(){
            const q=(document.getElementById('stockSearch')?.value||'').toLowerCase();
            const tbody=document.getElementById('stockTableBody')||document.getElementById('stockTable');
            if(!tbody) return;
            Array.from(tbody.querySelectorAll('tr')).forEach(tr=>{
                const nameCell=tr.querySelector('td');
                const name=nameCell?nameCell.textContent.toLowerCase():'';
                tr.style.display=name.includes(q)?'':'';
            });
        }
    
