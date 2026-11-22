<template>
  <AppLayout>
    <template #header-title>
      <div>
        <h1 class="text-base font-display font-semibold text-[#F5F5F3] tracking-tight">Admin Console</h1>
        <p class="text-xs text-[#8A8D96]">AI usage, user management, and platform logs</p>
      </div>
    </template>

    <div class="space-y-6 max-w-7xl mx-auto">
      <div
        role="tablist"
        aria-label="Admin sections"
        class="inline-flex flex-wrap border border-white/[0.12] divide-x divide-white/[0.1] bg-[#08080B] text-xs font-medium"
      >
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          role="tab"
          :aria-selected="activeTab === tab.id"
          @click="selectTab(tab.id)"
          :class="[
            'px-4 py-2 transition-colors',
            activeTab === tab.id
              ? 'bg-[#F5F5F3] text-[#050507] font-semibold'
              : 'text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.04]',
          ]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- TAB 1: AI USAGE -->
      <div v-if="activeTab === 'telemetry'" role="tabpanel" class="space-y-6">
        <SkeletonBlock v-if="loadingTelemetry" variant="kpi" :count="4" />

        <template v-else-if="telemetry">
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 border border-white/[0.11] divide-y sm:divide-y-0 sm:divide-x divide-white/[0.11] bg-[#08080B]">
            <div class="p-5 space-y-1.5">
              <span class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96]">Total AI Tokens</span>
              <div class="text-2xl font-display font-bold font-mono text-[#F5F5F3] tabular-nums">
                {{ telemetry.total_tokens.toLocaleString('en-US') }}
              </div>
              <p class="text-xs text-[#8A8D96] tabular-nums">{{ telemetry.total_narratives }} drafts generated</p>
            </div>

            <div class="p-5 space-y-1.5">
              <span class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96]">Monthly Estimated Cost</span>
              <div class="text-2xl font-display font-bold font-mono text-[#F5F5F3] tabular-nums">
                ${{ telemetry.estimated_cost_usd.toFixed(4) }}
              </div>
              <p class="text-xs text-[#8A8D96] tabular-nums">
                ≈ Rp {{ telemetry.estimated_cost_idr.toLocaleString('en-US') }}
              </p>
            </div>

            <div class="p-5 space-y-1.5">
              <span class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96]">Template Fallback Rate</span>
              <div class="text-2xl font-display font-bold font-mono text-amber-300 tabular-nums">
                {{ (telemetry.fallback_ratio * 100).toFixed(1) }}%
              </div>
              <p class="text-xs text-[#8A8D96] tabular-nums">{{ telemetry.fallback_count }} template fallbacks</p>
            </div>

            <div class="p-5 space-y-2">
              <span class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96]">Monthly Spend Limit</span>
              <div>
                <StatusBadge :status="telemetry.circuit_breaker_active ? 'TRIPPED' : 'NORMAL'" />
              </div>
              <p class="text-xs text-[#8A8D96] font-mono tabular-nums">
                Limit: ${{ telemetry.monthly_spend_ceiling_usd.toFixed(2) }}/mo
              </p>
            </div>
          </div>

          <!-- Spend Limit Gauge & Form -->
          <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-4">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <h2 class="text-sm font-display font-semibold text-[#F5F5F3]">
                Monthly AI Spend vs Limit (USD)
              </h2>
              <span class="text-xs font-mono text-[#D4D4D8] tabular-nums">
                ${{ telemetry.estimated_cost_usd.toFixed(4) }} / ${{ telemetry.monthly_spend_ceiling_usd.toFixed(2) }}
                ({{ spendPct.toFixed(1) }}%)
              </span>
            </div>

            <div class="h-2 bg-[#050507] border border-white/[0.1] overflow-hidden">
              <div
                :class="[
                  'h-full transition-all duration-500',
                  spendPct >= 100 ? 'bg-red-500' : spendPct >= 80 ? 'bg-amber-400' : 'bg-[#F5F5F3]',
                ]"
                :style="{ width: `${Math.min(100, spendPct)}%` }"
              ></div>
            </div>

            <form @submit.prevent="handleUpdateCeiling" class="flex flex-wrap items-center gap-2.5 text-xs pt-1">
              <label for="spend-ceiling-input" class="sr-only">Monthly spend limit in USD</label>
              <input
                id="spend-ceiling-input"
                v-model.number="ceilingInput"
                type="number"
                step="0.5"
                min="0.01"
                required
                class="input-glass w-48 px-3 py-2 font-mono text-xs tabular-nums"
              />
              <button
                type="submit"
                :disabled="updatingCeiling"
                class="btn-platinum px-4 py-2 text-xs disabled:opacity-50"
              >
                {{ updatingCeiling ? 'Saving...' : 'Save spend limit' }}
              </button>
            </form>
          </div>

          <!-- Per Workspace Table -->
          <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-3">
            <h3 class="text-sm font-display font-semibold text-[#F5F5F3]">Usage by Workspace</h3>
            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs">
                <thead class="border-b border-white/[0.1] font-mono uppercase text-[10px] tracking-wider text-[#8A8D96]">
                  <tr>
                    <th class="py-2 pr-4">Workspace</th>
                    <th class="py-2 px-4">Tokens</th>
                    <th class="py-2 px-4">Drafts</th>
                    <th class="py-2 px-4">Fallbacks</th>
                    <th class="py-2 pl-4 text-right">Estimated Cost</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-white/[0.08] font-mono">
                  <tr v-if="telemetry.by_workspace.length === 0">
                    <td colspan="5" class="py-6 text-center font-sans text-[#8A8D96]">
                      No AI token usage recorded yet.
                    </td>
                  </tr>
                  <tr v-for="ws in telemetry.by_workspace" :key="ws.workspace_id">
                    <td class="py-2.5 pr-4 font-sans font-medium text-[#F5F5F3]">{{ ws.workspace_name }}</td>
                    <td class="py-2.5 px-4 text-[#F5F5F3] tabular-nums">{{ ws.total_tokens.toLocaleString('en-US') }}</td>
                    <td class="py-2.5 px-4 text-[#D4D4D8] tabular-nums">{{ ws.narrative_count }}</td>
                    <td class="py-2.5 px-4 text-amber-300 tabular-nums">{{ ws.fallback_count }}</td>
                    <td class="py-2.5 pl-4 text-right text-[#D4D4D8] tabular-nums">
                      ${{ ws.estimated_cost_usd.toFixed(4) }} (Rp {{ ws.estimated_cost_idr.toLocaleString('en-US') }})
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </div>

      <!-- TAB 2: USERS -->
      <div v-if="activeTab === 'users'" role="tabpanel" class="border border-white/[0.11] bg-[#08080B] p-6 space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 class="text-sm sm:text-base font-display font-semibold text-[#F5F5F3] tabular-nums">
            Platform Users ({{ filteredUsers.length }})
          </h2>
          <div class="flex flex-wrap items-center gap-2 text-xs">
            <label for="admin-user-search" class="sr-only">Search name or email</label>
            <input
              id="admin-user-search"
              v-model.trim="userSearch"
              type="text"
              placeholder="Search name or email..."
              class="input-glass px-3 py-1.5 text-xs"
            />
            <label for="admin-user-status" class="sr-only">Filter user status</label>
            <select
              id="admin-user-status"
              v-model="userStatusFilter"
              @change="loadUsers(0)"
              class="input-glass px-3 py-1.5 text-xs"
            >
              <option value="">All statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="SUSPENDED">Suspended</option>
            </select>
          </div>
        </div>

        <SkeletonBlock v-if="loadingUsers" variant="table-row" :count="4" />

        <div v-else class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="border-b border-white/[0.1] font-mono uppercase text-[10px] tracking-wider text-[#8A8D96]">
              <tr>
                <th class="py-2 pr-3">User</th>
                <th class="py-2 px-3">Status</th>
                <th class="py-2 px-3">2FA</th>
                <th class="py-2 px-3">Workspaces</th>
                <th class="py-2 pl-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/[0.08]">
              <tr v-if="filteredUsers.length === 0">
                <td colspan="5" class="py-6 text-center text-[#8A8D96]">
                  No users match your search criteria.
                </td>
              </tr>
              <tr v-for="u in filteredUsers" :key="u.id">
                <td class="py-2.5 pr-3">
                  <div class="font-medium text-[#F5F5F3] flex items-center gap-1.5">
                    <span>{{ u.full_name }}</span>
                    <span
                      v-if="u.is_superadmin"
                      class="font-mono text-[10px] font-medium px-1.5 py-0.5 border border-white/[0.2] text-[#F5F5F3]"
                    >
                      Admin
                    </span>
                  </div>
                  <div class="text-[11px] font-mono text-[#8A8D96]">{{ u.email }}</div>
                </td>
                <td class="py-2.5 px-3">
                  <StatusBadge :status="u.status" />
                </td>
                <td class="py-2.5 px-3 text-[#D4D4D8]">
                  {{ u.mfa_enabled ? 'Enabled' : 'Off' }}
                </td>
                <td class="py-2.5 px-3 font-mono text-[#D4D4D8] tabular-nums">{{ u.workspace_count }}</td>
                <td class="py-2.5 pl-3 text-right">
                  <button
                    v-if="u.status === 'ACTIVE' && u.id !== session.state.user?.id"
                    type="button"
                    @click="openSuspendModal(u)"
                    class="btn-glass px-2.5 py-1 text-xs border-red-400/35 text-red-300 hover:bg-red-500/20 hover:text-red-200"
                  >
                    Suspend
                  </button>
                  <button
                    v-else-if="u.status !== 'ACTIVE'"
                    type="button"
                    @click="activateTarget = u"
                    class="btn-glass px-2.5 py-1 text-xs border-emerald-400/35 text-emerald-300 hover:bg-emerald-500/20 hover:text-emerald-200"
                  >
                    Activate
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="flex items-center justify-between pt-3 border-t border-white/[0.08] text-xs text-[#8A8D96] tabular-nums">
          <span>Page {{ Math.floor(userOffset / userLimit) + 1 }}</span>
          <div class="flex items-center gap-2">
            <button
              type="button"
              :disabled="userOffset === 0"
              @click="loadUsers(Math.max(0, userOffset - userLimit))"
              class="btn-glass px-3 py-1 text-xs disabled:opacity-40"
            >
              Previous
            </button>
            <button
              type="button"
              :disabled="users.length < userLimit"
              @click="loadUsers(userOffset + userLimit)"
              class="btn-glass px-3 py-1 text-xs disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      <!-- TAB 3: AUDIT LOGS -->
      <div v-if="activeTab === 'audits'" role="tabpanel" class="border border-white/[0.11] bg-[#08080B] p-6 space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 class="text-sm sm:text-base font-display font-semibold text-[#F5F5F3] tabular-nums">
            Global Activity Log ({{ auditTotal }})
          </h2>
          <div class="flex flex-wrap gap-2 text-xs">
            <label for="admin-audit-ws" class="sr-only">Filter workspace ID</label>
            <input
              id="admin-audit-ws"
              v-model.trim="auditWorkspaceFilter"
              type="text"
              placeholder="Workspace ID (optional)..."
              class="input-glass px-3 py-1.5 font-mono text-xs"
            />
            <label for="admin-audit-action" class="sr-only">Filter action</label>
            <input
              id="admin-audit-action"
              v-model.trim="auditActionFilter"
              type="text"
              placeholder="Filter action..."
              class="input-glass px-3 py-1.5 font-mono text-xs"
            />
            <button
              type="button"
              @click="loadAuditLogs(0)"
              class="btn-glass px-3.5 py-1.5 text-xs"
            >
              Filter
            </button>
          </div>
        </div>

        <SkeletonBlock v-if="loadingAudits" variant="table-row" :count="5" />

        <div v-else class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="border-b border-white/[0.1] font-mono uppercase text-[10px] tracking-wider text-[#8A8D96]">
              <tr>
                <th class="py-2 pr-3">Time</th>
                <th class="py-2 px-3">Action</th>
                <th class="py-2 px-3">Target</th>
                <th class="py-2 px-3">IP Address</th>
                <th class="py-2 pl-3">Details</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/[0.08] font-mono">
              <tr v-if="auditLogs.length === 0">
                <td colspan="5" class="py-6 text-center font-sans text-[#8A8D96]">
                  No activity logs match your filter.
                </td>
              </tr>
              <tr v-for="log in auditLogs" :key="log.id">
                <td class="py-2.5 pr-3 text-[#8A8D96] whitespace-nowrap font-sans">
                  {{ new Date(log.created_at).toLocaleString('en-US') }}
                </td>
                <td class="py-2.5 px-3 text-amber-300 font-semibold">{{ log.action }}</td>
                <td class="py-2.5 px-3 text-[#D4D4D8]">{{ log.target_entity }}</td>
                <td class="py-2.5 px-3 text-[#8A8D96]">{{ log.ip_address }}</td>
                <td class="py-2.5 pl-3">
                  <button
                    type="button"
                    @click="selectedAuditLog = log"
                    class="text-left text-[11px] text-[#D4D4D8] hover:text-[#F5F5F3] max-w-xs truncate block underline-offset-4 hover:underline"
                  >
                    {{ JSON.stringify(log.details) }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="flex items-center justify-between pt-3 border-t border-white/[0.08] text-xs text-[#8A8D96] tabular-nums">
          <span>Showing {{ auditLogs.length }} of {{ auditTotal }} entries</span>
          <div class="flex items-center gap-2">
            <button
              type="button"
              :disabled="auditOffset === 0"
              @click="loadAuditLogs(Math.max(0, auditOffset - auditLimit))"
              class="btn-glass px-3 py-1 text-xs disabled:opacity-40"
            >
              Previous
            </button>
            <button
              type="button"
              :disabled="auditOffset + auditLimit >= auditTotal"
              @click="loadAuditLogs(auditOffset + auditLimit)"
              class="btn-glass px-3 py-1 text-xs disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      <!-- TAB 4: WORKSPACES & PLANS -->
      <div v-if="activeTab === 'workspaces'" role="tabpanel" class="space-y-6">
        <!-- Enterprise Inquiries Queue -->
        <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <h2 class="text-sm sm:text-base font-display font-semibold text-[#F5F5F3] tabular-nums">
              Enterprise Inquiries ({{ inquiries.length }})
            </h2>
            <select
              v-model="inquiryStatusFilter"
              @change="loadWorkspacesAndInquiries"
              class="input-glass px-3 py-1.5 text-xs"
            >
              <option value="">All inquiry statuses</option>
              <option value="NEW">New</option>
              <option value="CONTACTED">Contacted</option>
              <option value="PROVISIONED">Provisioned</option>
              <option value="DECLINED">Declined</option>
            </select>
          </div>

          <SkeletonBlock v-if="loadingWorkspaces" variant="table-row" :count="3" />

          <div v-else class="overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead class="border-b border-white/[0.1] font-mono uppercase text-[10px] tracking-wider text-[#8A8D96]">
                <tr>
                  <th class="py-2 pr-3">Company / Contact</th>
                  <th class="py-2 px-3">Team / Est. Reports</th>
                  <th class="py-2 px-3">Status</th>
                  <th class="py-2 px-3">Requirements</th>
                  <th class="py-2 pl-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/[0.08]">
                <tr v-if="inquiries.length === 0">
                  <td colspan="5" class="py-6 text-center text-[#8A8D96]">
                    No Enterprise inquiries found.
                  </td>
                </tr>
                <tr v-for="inq in inquiries" :key="inq.id">
                  <td class="py-2.5 pr-3">
                    <div class="font-medium text-[#F5F5F3]">{{ inq.company_name }}</div>
                    <div class="text-[11px] font-mono text-[#8A8D96]">
                      {{ inq.contact_name }} ({{ inq.contact_email }})
                    </div>
                  </td>
                  <td class="py-2.5 px-3 font-mono text-[#D4D4D8] tabular-nums">
                    {{ inq.team_size }} · {{ inq.estimated_monthly_reports ?? '-' }}/mo
                  </td>
                  <td class="py-2.5 px-3">
                    <select
                      :value="inq.status"
                      @change="handleInquiryStatusChange(inq, $event)"
                      class="input-glass px-2 py-1 text-xs"
                    >
                      <option value="NEW">NEW</option>
                      <option value="CONTACTED">CONTACTED</option>
                      <option value="PROVISIONED">PROVISIONED</option>
                      <option value="DECLINED">DECLINED</option>
                    </select>
                  </td>
                  <td class="py-2.5 px-3 text-[#D4D4D8] max-w-xs truncate" :title="inq.requirements">
                    {{ inq.requirements }}
                  </td>
                  <td class="py-2.5 pl-3 text-right">
                    <button
                      v-if="inq.workspace_id"
                      type="button"
                      @click="quickProvisionFromInquiry(inq)"
                      class="btn-glass px-2.5 py-1 text-xs border-emerald-400/35 text-emerald-300 hover:bg-emerald-500/20"
                    >
                      Provision Enterprise
                    </button>
                    <span v-else class="font-mono text-[11px] text-[#8A8D96]">No WS linked</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Workspace Subscriptions -->
        <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <h2 class="text-sm sm:text-base font-display font-semibold text-[#F5F5F3] tabular-nums">
              Workspaces &amp; Plan Limits ({{ workspaceSubs.length }})
            </h2>
            <select
              v-model="workspaceTierFilter"
              @change="loadWorkspacesAndInquiries"
              class="input-glass px-3 py-1.5 text-xs"
            >
              <option value="">All tiers</option>
              <option value="FREE">Free</option>
              <option value="PRO">Pro</option>
              <option value="ENTERPRISE">Enterprise</option>
            </select>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead class="border-b border-white/[0.1] font-mono uppercase text-[10px] tracking-wider text-[#8A8D96]">
                <tr>
                  <th class="py-2 pr-3">Workspace</th>
                  <th class="py-2 px-3">Tier</th>
                  <th class="py-2 px-3">PDF Quota</th>
                  <th class="py-2 px-3">CLI Batch Limit</th>
                  <th class="py-2 px-3">Managers</th>
                  <th class="py-2 pl-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/[0.08]">
                <tr v-for="ws in workspaceSubs" :key="ws.workspace_id">
                  <td class="py-2.5 pr-3">
                    <div class="font-medium text-[#F5F5F3]">{{ ws.workspace_name }}</div>
                    <div class="text-[11px] font-mono text-[#8A8D96]">{{ ws.workspace_id }}</div>
                  </td>
                  <td class="py-2.5 px-3"><StatusBadge :status="ws.tier" /></td>
                  <td class="py-2.5 px-3 font-mono text-[#D4D4D8] tabular-nums">
                    {{ ws.reports_used_this_month }} / {{ ws.is_unlimited ? 'Unlimited' : ws.monthly_report_quota }}
                  </td>
                  <td class="py-2.5 px-3 font-mono text-[#D4D4D8] tabular-nums">
                    {{ ws.custom_batch_limit ?? (ws.tier === 'FREE' ? 50 : ws.tier === 'ENTERPRISE' ? 2000 : 500) }}
                  </td>
                  <td class="py-2.5 px-3 font-mono text-[#8A8D96]">
                    {{ ws.manager_emails.join(', ') || '-' }}
                  </td>
                  <td class="py-2.5 pl-3 text-right">
                    <button
                      type="button"
                      @click="openSubscriptionModal(ws)"
                      class="btn-glass px-2.5 py-1 text-xs"
                    >
                      Manage Plan
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Workspace Subscription Override Modal -->
    <BaseModal
      :open="Boolean(subOverrideTarget)"
      :title="`Manage Plan: ${subOverrideTarget?.workspace_name || ''}`"
      subtitle="Override subscription tier, monthly PDF quota, or Enterprise CLI batch limit."
      max-width="md"
      @close="subOverrideTarget = null"
    >
      <form id="sub-override-form" @submit.prevent="confirmSubscriptionOverride" class="space-y-3.5 text-xs">
        <div class="space-y-1">
          <label for="sub-tier" class="text-[#D4D4D8] font-medium block">Tier</label>
          <select id="sub-tier" v-model="subForm.tier" class="input-glass w-full px-3 py-2 text-xs">
            <option value="FREE">FREE</option>
            <option value="PRO">PRO</option>
            <option value="ENTERPRISE">ENTERPRISE</option>
          </select>
        </div>

        <label class="flex items-center gap-2 text-[#D4D4D8] cursor-pointer">
          <input type="checkbox" v-model="subForm.unlimited" class="bg-[#050507] border-white/25" />
          <span>Unlimited monthly PDF reports (-1)</span>
        </label>

        <div v-if="!subForm.unlimited" class="space-y-1">
          <label for="sub-quota" class="text-[#D4D4D8] font-medium block">Monthly Report Quota</label>
          <input
            id="sub-quota"
            v-model.number="subForm.monthly_report_quota"
            type="number"
            min="0"
            max="100000"
            required
            class="input-glass w-full px-3 py-2 text-xs font-mono"
          />
        </div>

        <div class="space-y-1">
          <label for="sub-batch" class="text-[#D4D4D8] font-medium block">
            Custom CLI Batch Limit (optional, 50-50000)
          </label>
          <input
            id="sub-batch"
            v-model.number="subForm.custom_batch_limit"
            type="number"
            min="50"
            max="50000"
            placeholder="2000 for Enterprise default"
            class="input-glass w-full px-3 py-2 text-xs font-mono"
          />
        </div>

        <div class="space-y-1">
          <label for="sub-reason" class="text-[#D4D4D8] font-medium block">Audit Reason</label>
          <input
            id="sub-reason"
            v-model.trim="subForm.reason"
            type="text"
            required
            minlength="3"
            placeholder="Enterprise contract provisioned..."
            class="input-glass w-full px-3 py-2 text-xs"
          />
        </div>
      </form>
      <template #footer>
        <button type="button" @click="subOverrideTarget = null" class="btn-glass px-4 py-2 text-xs">
          Cancel
        </button>
        <button
          type="submit"
          form="sub-override-form"
          :disabled="savingSubOverride"
          class="btn-platinum px-4 py-2 text-xs disabled:opacity-50"
        >
          {{ savingSubOverride ? 'Saving...' : 'Save Plan' }}
        </button>
      </template>
    </BaseModal>

    <!-- Suspend Modal -->
    <BaseModal
      :open="Boolean(suspendTarget)"
      :title="`Suspend User: ${suspendTarget?.email || ''}`"
      subtitle="Suspending an account immediately revokes active sessions and CLI API keys."
      max-width="md"
      @close="suspendTarget = null"
    >
      <form id="suspend-user-form" @submit.prevent="confirmSuspend" class="space-y-3 text-xs">
        <label for="suspend-reason" class="font-medium text-[#D4D4D8] block">
          Reason for suspension (recorded in audit log)
        </label>
        <textarea
          id="suspend-reason"
          v-model.trim="suspendReason"
          rows="3"
          required
          minlength="3"
          placeholder="Policy violation or suspicious activity..."
          class="input-glass w-full p-3 text-xs"
        ></textarea>
      </form>
      <template #footer>
        <button
          type="button"
          @click="suspendTarget = null"
          class="btn-glass px-4 py-2 text-xs"
        >
          Cancel
        </button>
        <button
          type="submit"
          form="suspend-user-form"
          :disabled="suspending"
          class="bg-red-600 hover:bg-red-500 text-white px-4 py-2 text-xs font-semibold transition-colors disabled:opacity-50"
        >
          {{ suspending ? 'Suspending...' : 'Suspend & Revoke Access' }}
        </button>
      </template>
    </BaseModal>

    <!-- Activate Confirmation -->
    <ConfirmDialog
      :open="Boolean(activateTarget)"
      title="Reactivate User?"
      :message="`Restore active status for '${activateTarget?.email || ''}'?`"
      confirm-text="Activate"
      variant="primary"
      :loading="activating"
      @confirm="confirmActivateUser"
      @cancel="activateTarget = null"
    />

    <!-- Audit Detail Modal -->
    <BaseModal
      :open="Boolean(selectedAuditLog)"
      title="Activity Details"
      max-width="lg"
      @close="selectedAuditLog = null"
    >
      <div v-if="selectedAuditLog" class="space-y-3 text-xs font-mono">
        <dl class="grid grid-cols-2 border border-white/[0.1] divide-x divide-white/[0.1] bg-[#050507]">
          <div class="p-3">
            <dt class="font-sans text-[#8A8D96] text-xs">Action</dt>
            <dd class="text-amber-300 font-semibold mt-0.5">{{ selectedAuditLog.action }}</dd>
          </div>
          <div class="p-3">
            <dt class="font-sans text-[#8A8D96] text-xs">Workspace ID</dt>
            <dd class="text-[#F5F5F3] break-all mt-0.5">{{ selectedAuditLog.workspace_id }}</dd>
          </div>
        </dl>
        <pre class="p-3.5 bg-[#050507] border border-white/[0.1] text-[#D4D4D8] overflow-x-auto max-h-72">{{
          JSON.stringify(selectedAuditLog.details, null, 2)
        }}</pre>
      </div>
    </BaseModal>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import {
  api,
  type AdminUserSummary,
  type AdminWorkspaceSubscriptionSummary,
  type AITelemetryResponse,
  type AuditLogEntry,
  type EnterpriseInquiryResponse,
  type EnterpriseInquiryStatus,
} from '@/services/api'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'

const route = useRoute()
const router = useRouter()

const tabs = [
  { id: 'telemetry', label: 'AI Usage' },
  { id: 'users', label: 'Users' },
  { id: 'workspaces', label: 'Workspaces & Plans' },
  { id: 'audits', label: 'Audit Logs' },
] as const
type AdminTabId = (typeof tabs)[number]['id']
const activeTab = ref<AdminTabId>('telemetry')

watch(
  () => route.query.tab,
  (tabParam) => {
    if (tabParam === 'users') {
      activeTab.value = 'users'
    } else if (tabParam === 'workspaces') {
      activeTab.value = 'workspaces'
    } else if (tabParam === 'audits') {
      activeTab.value = 'audits'
    } else {
      activeTab.value = 'telemetry'
    }
  },
  { immediate: true }
)

const selectTab = (id: AdminTabId) => {
  activeTab.value = id
  void router.replace({ path: '/app/admin', query: id === 'telemetry' ? {} : { tab: id } })
}

const telemetry = ref<AITelemetryResponse | null>(null)
const loadingTelemetry = ref(false)
const updatingCeiling = ref(false)
const ceilingInput = ref(100)

const spendPct = computed(() => {
  if (!telemetry.value || telemetry.value.monthly_spend_ceiling_usd <= 0) return 0
  return (telemetry.value.estimated_cost_usd / telemetry.value.monthly_spend_ceiling_usd) * 100
})

const users = ref<AdminUserSummary[]>([])
const loadingUsers = ref(false)
const userSearch = ref('')
const userStatusFilter = ref('')
const userOffset = ref(0)
const userLimit = 50
const suspendTarget = ref<AdminUserSummary | null>(null)
const suspendReason = ref('')
const suspending = ref(false)
const activateTarget = ref<AdminUserSummary | null>(null)
const activating = ref(false)

const filteredUsers = computed(() => {
  const q = userSearch.value.toLowerCase()
  if (!q) return users.value
  return users.value.filter(
    (u) => u.full_name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
  )
})

const auditLogs = ref<AuditLogEntry[]>([])
const loadingAudits = ref(false)
const auditTotal = ref(0)
const auditOffset = ref(0)
const auditLimit = 50
const auditWorkspaceFilter = ref('')
const auditActionFilter = ref('')
const selectedAuditLog = ref<AuditLogEntry | null>(null)

async function loadTelemetry(): Promise<void> {
  loadingTelemetry.value = true
  try {
    telemetry.value = await api.admin.getAiTelemetry()
    ceilingInput.value = telemetry.value.monthly_spend_ceiling_usd
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to load AI usage metrics.')
  } finally {
    loadingTelemetry.value = false
  }
}

async function loadUsers(offset = 0): Promise<void> {
  userOffset.value = offset
  loadingUsers.value = true
  try {
    users.value = await api.admin.listUsers({
      status: userStatusFilter.value || undefined,
      limit: userLimit,
      offset,
    })
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to load users.')
  } finally {
    loadingUsers.value = false
  }
}

async function loadAuditLogs(offset = 0): Promise<void> {
  auditOffset.value = offset
  loadingAudits.value = true
  try {
    const res = await api.admin.listAuditLogs({
      workspace_id: auditWorkspaceFilter.value || undefined,
      action: auditActionFilter.value || undefined,
      limit: auditLimit,
      offset,
    })
    auditLogs.value = res.items
    auditTotal.value = res.total
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to load global audit logs.')
  } finally {
    loadingAudits.value = false
  }
}

onMounted(() => {
  void Promise.all([
    loadTelemetry(),
    loadUsers(0),
    loadAuditLogs(0),
    loadWorkspacesAndInquiries(),
  ])
})

const workspaceSubs = ref<AdminWorkspaceSubscriptionSummary[]>([])
const inquiries = ref<EnterpriseInquiryResponse[]>([])
const loadingWorkspaces = ref(false)
const workspaceTierFilter = ref('')
const inquiryStatusFilter = ref('')
const subOverrideTarget = ref<AdminWorkspaceSubscriptionSummary | null>(null)
const savingSubOverride = ref(false)
const subForm = ref<{
  tier: 'FREE' | 'PRO' | 'ENTERPRISE'
  unlimited: boolean
  monthly_report_quota: number
  custom_batch_limit: number | null
  reason: string
}>({
  tier: 'ENTERPRISE',
  unlimited: true,
  monthly_report_quota: 30,
  custom_batch_limit: 2000,
  reason: '',
})

async function loadWorkspacesAndInquiries(): Promise<void> {
  loadingWorkspaces.value = true
  try {
    const [wsList, inqList] = await Promise.all([
      api.admin.listWorkspaces({ tier: workspaceTierFilter.value || undefined }),
      api.admin.listEnterpriseInquiries({ status: inquiryStatusFilter.value || undefined }),
    ])
    workspaceSubs.value = wsList
    inquiries.value = inqList
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to load workspace plans.')
  } finally {
    loadingWorkspaces.value = false
  }
}

const openSubscriptionModal = (ws: AdminWorkspaceSubscriptionSummary) => {
  subOverrideTarget.value = ws
  subForm.value = {
    tier: (ws.tier === 'PRO' || ws.tier === 'ENTERPRISE' ? ws.tier : 'FREE') as
      | 'FREE'
      | 'PRO'
      | 'ENTERPRISE',
    unlimited: ws.is_unlimited || ws.monthly_report_quota < 0,
    monthly_report_quota: ws.monthly_report_quota < 0 ? 100 : ws.monthly_report_quota,
    custom_batch_limit: ws.custom_batch_limit ?? null,
    reason: '',
  }
}

const quickProvisionFromInquiry = (inq: EnterpriseInquiryResponse) => {
  const target = workspaceSubs.value.find((w) => w.workspace_id === inq.workspace_id)
  if (!target) return
  subOverrideTarget.value = target
  subForm.value = {
    tier: 'ENTERPRISE',
    unlimited: true,
    monthly_report_quota: 500,
    custom_batch_limit: 2000,
    reason: `Provisioned via Enterprise inquiry ${inq.id}`,
  }
}

const handleInquiryStatusChange = async (inq: EnterpriseInquiryResponse, event: Event) => {
  const select = event.target as HTMLSelectElement
  const nextStatus = select.value as EnterpriseInquiryStatus
  try {
    await api.admin.updateEnterpriseInquiry(inq.id, { status: nextStatus })
    inq.status = nextStatus
    toast.success(`Inquiry status updated to ${nextStatus}.`)
  } catch (err: unknown) {
    select.value = inq.status
    toast.error(err instanceof Error ? err.message : 'Unable to update inquiry status.')
  }
}

const confirmSubscriptionOverride = async () => {
  if (!subOverrideTarget.value) return
  savingSubOverride.value = true
  try {
    await api.admin.overrideWorkspaceSubscription(subOverrideTarget.value.workspace_id, {
      tier: subForm.value.tier,
      monthly_report_quota: subForm.value.unlimited ? -1 : subForm.value.monthly_report_quota,
      custom_batch_limit: subForm.value.custom_batch_limit || null,
      reason: subForm.value.reason,
    })
    subOverrideTarget.value = null
    await Promise.all([loadWorkspacesAndInquiries(), loadAuditLogs(auditOffset.value)])
    toast.success('Workspace plan updated.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to update workspace plan.')
  } finally {
    savingSubOverride.value = false
  }
}

const handleUpdateCeiling = async () => {
  updatingCeiling.value = true
  try {
    telemetry.value = await api.admin.updateSpendCeiling(ceilingInput.value)
    toast.success(`Monthly spend limit updated to $${ceilingInput.value.toFixed(2)}.`)
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to update spend limit.')
  } finally {
    updatingCeiling.value = false
  }
}

const openSuspendModal = (u: AdminUserSummary) => {
  suspendTarget.value = u
  suspendReason.value = ''
}

const confirmSuspend = async () => {
  if (!suspendTarget.value) return
  suspending.value = true
  try {
    await api.admin.suspendUser(suspendTarget.value.id, suspendReason.value)
    suspendTarget.value = null
    await Promise.all([loadUsers(userOffset.value), loadAuditLogs(auditOffset.value)])
    toast.success('User suspended and all active sessions and API keys revoked.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to suspend user.')
  } finally {
    suspending.value = false
  }
}

const confirmActivateUser = async () => {
  if (!activateTarget.value) return
  activating.value = true
  try {
    await api.admin.activateUser(activateTarget.value.id)
    activateTarget.value = null
    await Promise.all([loadUsers(userOffset.value), loadAuditLogs(auditOffset.value)])
    toast.success('User reactivated.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to activate user.')
  } finally {
    activating.value = false
  }
}
</script>
