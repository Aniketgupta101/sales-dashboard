/**
 * app.js — Sales Dashboard Frontend Logic
 *
 * Fetches data from /api/dashboard and /api/filters, renders KPI cards
 * and Chart.js charts. All revenue formatted in INR (en-IN locale).
 */

// ── Formatting helpers ──────────────────────────────────────────────

const fmtINR = (val) =>
    "₹" + Number(val).toLocaleString("en-IN", { maximumFractionDigits: 0 });

const fmtINR2 = (val) =>
    "₹" + Number(val).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const fmtNumber = (val) =>
    Number(val).toLocaleString("en-IN");

// ── Color palette ───────────────────────────────────────────────────

const COLORS = {
    primary: "#0d9488",
    primaryLight: "#14b8a6",
    accent: "#2563eb",
    accentLight: "#3b82f6",
    teal50: "rgba(13, 148, 136, 0.1)",
    teal200: "rgba(13, 148, 136, 0.3)",
    palette: [
        "#0d9488", "#2563eb", "#f59e0b", "#ef4444",
        "#8b5cf6", "#ec4899", "#10b981", "#f97316",
        "#6366f1", "#14b8a6"
    ],
    paletteBg: [
        "rgba(13,148,136,0.75)", "rgba(37,99,235,0.75)", "rgba(245,158,11,0.75)",
        "rgba(239,68,68,0.75)", "rgba(139,92,246,0.75)", "rgba(236,72,153,0.75)",
        "rgba(16,185,129,0.75)", "rgba(249,115,22,0.75)", "rgba(99,102,241,0.75)",
        "rgba(20,184,166,0.75)"
    ],
};

// ── Chart instances (destroyed before re-create) ────────────────────

let charts = {};

function destroyCharts() {
    Object.values(charts).forEach((c) => { if (c) c.destroy(); });
    charts = {};
}

// ── UI state helpers ────────────────────────────────────────────────

function showLoading(show) {
    document.getElementById("loading").style.display = show ? "flex" : "none";
}

function showError(msg) {
    const banner = document.getElementById("error-banner");
    document.getElementById("error-message").textContent = msg;
    banner.style.display = "flex";
}

function hideError() {
    document.getElementById("error-banner").style.display = "none";
}

// ── Populate filter dropdowns ───────────────────────────────────────

async function loadFilters() {
    try {
        const res = await fetch("/api/filters");
        if (!res.ok) throw new Error("Failed to load filters");
        const data = await res.json();

        populateSelect("filter-category", data.categories);
        populateSelect("filter-segment", data.segments);
        populateSelect("filter-city", data.cities);
        populateSelect("filter-status", data.statuses);
    } catch (e) {
        console.error("Filter load error:", e);
    }
}

function populateSelect(id, options) {
    const sel = document.getElementById(id);
    // Keep the first "All" option
    while (sel.options.length > 1) sel.remove(1);
    options.forEach((opt) => {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = opt;
        sel.appendChild(o);
    });
}

// ── Build query string from filters ─────────────────────────────────

function getFilterParams() {
    const params = new URLSearchParams();
    const from = document.getElementById("filter-from").value;
    const to = document.getElementById("filter-to").value;
    const category = document.getElementById("filter-category").value;
    const segment = document.getElementById("filter-segment").value;
    const city = document.getElementById("filter-city").value;
    const status = document.getElementById("filter-status").value;

    if (from) params.set("from", from);
    if (to) params.set("to", to);
    if (category) params.set("category", category);
    if (segment) params.set("segment", segment);
    if (city) params.set("city", city);
    if (status) params.set("status", status);

    return params.toString();
}

// ── Fetch dashboard data and render ─────────────────────────────────

async function fetchDashboard() {
    hideError();
    showLoading(true);

    try {
        const qs = getFilterParams();
        const res = await fetch(`/api/dashboard?${qs}`);
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        const data = await res.json();

        renderKPIs(data.kpis);
        destroyCharts();
        renderMonthlyChart(data.monthly);
        renderCategoryChart(data.by_category);
        renderStatusChart(data.by_status);
        renderSegmentChart(data.by_segment);
        renderProductsChart(data.top_products);
        renderCityChart(data.by_city);
    } catch (e) {
        console.error("Dashboard fetch error:", e);
        showError("Failed to load dashboard data. Please try again.");
    } finally {
        showLoading(false);
    }
}

// ── KPI rendering ───────────────────────────────────────────────────

function renderKPIs(kpis) {
    document.getElementById("kpi-revenue").textContent = fmtINR(kpis.net_revenue);
    document.getElementById("kpi-orders").textContent = fmtNumber(kpis.total_orders);
    document.getElementById("kpi-customers").textContent = fmtNumber(kpis.unique_customers);
    document.getElementById("kpi-aov").textContent =
        kpis.avg_order_value !== null ? fmtINR2(kpis.avg_order_value) : "—";
    document.getElementById("kpi-repeat").textContent = fmtNumber(kpis.repeat_customers);
}

// ── Chart rendering ─────────────────────────────────────────────────

function renderMonthlyChart(data) {
    const ctx = document.getElementById("chart-monthly").getContext("2d");
    const labels = data.map((d) => {
        const [y, m] = d.month.split("-");
        return new Date(y, m - 1).toLocaleString("en-IN", { month: "short", year: "numeric" });
    });

    charts.monthly = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Revenue",
                data: data.map((d) => d.revenue),
                borderColor: COLORS.primary,
                backgroundColor: COLORS.teal50,
                fill: true,
                tension: 0.3,
                pointBackgroundColor: COLORS.primary,
                pointRadius: 5,
                pointHoverRadius: 7,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => fmtINR(ctx.parsed.y),
                    },
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (v) => "₹" + (v / 1000).toFixed(0) + "K",
                    },
                },
            },
        },
    });
}

function renderCategoryChart(data) {
    const ctx = document.getElementById("chart-category").getContext("2d");
    charts.category = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: data.map((d) => d.label),
            datasets: [{
                data: data.map((d) => d.revenue),
                backgroundColor: COLORS.paletteBg.slice(0, data.length),
                borderColor: COLORS.palette.slice(0, data.length),
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: { label: (ctx) => `${ctx.label}: ${fmtINR(ctx.parsed)}` },
                },
                legend: { position: "right" },
            },
        },
    });
}

function renderStatusChart(data) {
    const statusColors = {
        Completed: "#10b981",
        Returned: "#f59e0b",
        Cancelled: "#ef4444",
    };
    const ctx = document.getElementById("chart-status").getContext("2d");
    charts.status = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: data.map((d) => d.label),
            datasets: [{
                data: data.map((d) => d.orders),
                backgroundColor: data.map((d) => statusColors[d.label] || "#94a3b8"),
                borderWidth: 2,
                borderColor: "#fff",
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "right" },
                tooltip: {
                    callbacks: { label: (ctx) => `${ctx.label}: ${ctx.parsed} orders` },
                },
            },
        },
    });
}

function renderSegmentChart(data) {
    const ctx = document.getElementById("chart-segment").getContext("2d");
    charts.segment = new Chart(ctx, {
        type: "bar",
        data: {
            labels: data.map((d) => d.label),
            datasets: [{
                label: "Revenue",
                data: data.map((d) => d.revenue),
                backgroundColor: COLORS.paletteBg.slice(0, data.length),
                borderColor: COLORS.palette.slice(0, data.length),
                borderWidth: 2,
                borderRadius: 6,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: { label: (ctx) => fmtINR(ctx.parsed.y) },
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: (v) => "₹" + (v / 1000).toFixed(0) + "K" },
                },
            },
        },
    });
}

function renderProductsChart(data) {
    const ctx = document.getElementById("chart-products").getContext("2d");
    charts.products = new Chart(ctx, {
        type: "bar",
        data: {
            labels: data.map((d) => d.label),
            datasets: [{
                label: "Revenue",
                data: data.map((d) => d.revenue),
                backgroundColor: COLORS.paletteBg.slice(0, data.length),
                borderColor: COLORS.palette.slice(0, data.length),
                borderWidth: 2,
                borderRadius: 6,
            }],
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: { label: (ctx) => fmtINR(ctx.parsed.x) },
                },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { callback: (v) => "₹" + (v / 1000).toFixed(0) + "K" },
                },
            },
        },
    });
}

function renderCityChart(data) {
    const ctx = document.getElementById("chart-city").getContext("2d");
    charts.city = new Chart(ctx, {
        type: "bar",
        data: {
            labels: data.map((d) => d.label),
            datasets: [{
                label: "Revenue",
                data: data.map((d) => d.revenue),
                backgroundColor: COLORS.teal200,
                borderColor: COLORS.primary,
                borderWidth: 1,
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: { label: (ctx) => fmtINR(ctx.parsed.y) },
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: (v) => "₹" + (v / 1000).toFixed(0) + "K" },
                },
                x: {
                    ticks: { maxRotation: 45 },
                },
            },
        },
    });
}

// ── Event listeners ─────────────────────────────────────────────────

document.getElementById("btn-apply").addEventListener("click", fetchDashboard);

document.getElementById("btn-reset").addEventListener("click", () => {
    document.getElementById("filter-from").value = "2026-01-01";
    document.getElementById("filter-to").value = "2026-06-30";
    document.getElementById("filter-category").value = "";
    document.getElementById("filter-segment").value = "";
    document.getElementById("filter-city").value = "";
    document.getElementById("filter-status").value = "";
    fetchDashboard();
});

// ── Init ────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", async () => {
    await loadFilters();
    await fetchDashboard();
});
