"""Update frontend files for TASK-121."""
from pathlib import Path

# 1. Update frontend/index.html
index_path = Path("frontend/index.html")
content = index_path.read_text(encoding="utf-8")

target_btn = """        <!-- Nạp tiền Quick Action (TASK-120) -->
        <button
          type="button"
          id="topbar-deposit-btn"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-black bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white shadow-sm transition-all hover:scale-105 active:scale-95 cursor-pointer"
          onclick="window.location.hash = '#/student/wallet'"
          title="Nạp số dư tài khoản qua PayOS"
        >
          <span class="material-symbols-outlined text-[16px]">add_circle</span>
          <span class="hidden sm:inline">Nạp tiền</span>
        </button>"""

replacement_wallet = """        <!-- Topbar Wallet Quick Action & Dropdown (TASK-121) -->
        <div class="relative" id="topbar-wallet-wrapper">
          <button
            type="button"
            id="topbar-wallet-btn"
            class="group flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5] dark:bg-[#202020] hover:bg-[#F4F1EA] dark:hover:bg-[#262524] hover:border-emerald-500 text-[#222120] dark:text-[#EDEDEB] text-xs font-bold transition-all shadow-2xs select-none cursor-pointer"
            title="Ví tài khoản & Nạp tiền"
            aria-expanded="false"
            aria-haspopup="true"
            aria-controls="topbar-wallet-dropdown"
          >
            <span class="material-symbols-outlined text-[17px] text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform">account_balance_wallet</span>
            <span>Ví</span>
            <span class="material-symbols-outlined text-[15px] text-[#8F8E8A] dark:text-[#6D6C68] transition-transform duration-200" id="topbar-wallet-chevron">expand_more</span>
          </button>

          <!-- Minimalist Wallet Dropdown Menu -->
          <div
            id="topbar-wallet-dropdown"
            class="hidden absolute right-0 mt-2 w-56 rounded-2xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#1E1E1E] shadow-xl p-3.5 space-y-3 z-50 animate-scale-in"
            role="menu"
          >
            <div class="space-y-1">
              <div class="text-[11px] font-semibold text-slate-500 dark:text-slate-400">Số dư hiện có</div>
              <div class="text-lg font-black font-mono text-emerald-600 dark:text-emerald-400" id="topbar-wallet-balance-val">
                ...
              </div>
            </div>
            <button
              type="button"
              id="topbar-wallet-deposit-action"
              class="w-full c-btn c-btn-primary py-2 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 cursor-pointer shadow-sm hover:shadow-md transition-all"
            >
              <span class="material-symbols-outlined text-[16px]">add_circle</span>
              <span>Nạp tiền</span>
            </button>
          </div>
        </div>"""

norm_content = content.replace("\r\n", "\n")
norm_target = target_btn.replace("\r\n", "\n")
norm_replacement = replacement_wallet.replace("\r\n", "\n")

if norm_target in norm_content:
    norm_content = norm_content.replace(norm_target, norm_replacement)
    index_path.write_text(norm_content.replace("\n", "\r\n"), encoding="utf-8")
    print("index.html successfully updated")
else:
    print("ERROR: target button not found in index.html")
