<template>
  <AppLayout :pipeline-step="3">
    <template #header-title>
      <div>
        <h1 class="text-base font-display font-semibold text-[#F5F5F3] tracking-tight">
          Findings
        </h1>
        <p class="text-xs text-[#8A8D96] truncate">
          {{ activeProject ? activeProject.name : 'Select a project' }}
        </p>
      </div>
    </template>

    <div class="space-y-5 max-w-7xl mx-auto">
      <EmptyState
        v-if="!activeProject"
        :icon="FolderGit2"
        title="No active project"
        description="Create or select a project first to review findings and technical proof."
        action-label="Open Projects"
        action-to="/app/projects"
      />

      <template v-else>
        <!-- Summary Metrics & Action Bar -->
        <div
          class="flex flex-wrap items-center justify-between gap-3 p-4 border border-white/[0.11] bg-[#08080B]"
        >
          <div class="flex flex-wrap items-center gap-2 font-mono text-[11px] uppercase tracking-wider">
            <span class="px-2.5 py-1 bg-[#050507] border border-white/[0.12] text-[#D4D4D8] tabular-nums">
              Total: {{ summary.total }}
            </span>
            <span class="px-2.5 py-1 bg-[#050507] border border-white/[0.2] text-[#F5F5F3] tabular-nums">
              In Report: {{ summary.curated }}
            </span>
            <span class="px-2.5 py-1 bg-red-500/10 border border-red-400/25 text-red-300 tabular-nums">
              Out of Scope: {{ summary.quarantined }}
            </span>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <button
              type="button"
              @click="showCvssModal = true"
              class="btn-glass px-3 py-1.5 text-xs"
            >
              <Calculator class="h-3.5 w-3.5" aria-hidden="true" />
              <span>CVSS Calculator</span>
            </button>

            <button
              v-if="canTriage"
              type="button"
              @click="openManualModal"
              class="btn-glass px-3.5 py-1.5 text-xs"
            >
              <Plus class="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />
              <span>Add Finding</span>
            </button>

            <router-link
              to="/app/ai-review"
              class="btn-platinum px-3.5 py-1.5 text-xs tabular-nums"
            >
              <span>Continue to Draft ({{ summary.curated }})</span>
              <ArrowRight class="h-3.5 w-3.5" aria-hidden="true" />
            </router-link>
          </div>
        </div>

        <!-- Filters Toolbar -->
        <div
          class="flex flex-wrap items-center justify-between gap-3 p-4 border border-white/[0.11] bg-[#08080B]"
        >
          <div class="flex flex-wrap items-center gap-2.5 text-xs">
            <label for="filter-severity" class="sr-only">Filter by severity</label>
            <select
              id="filter-severity"
              v-model="severityFilter"
              @change="onFilterChanged"
              class="input-glass px-2.5 py-1.5 text-xs"
            >
              <option value="">All severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
              <option value="INFO">Info</option>
            </select>

            <label for="filter-status" class="sr-only">Filter by status</label>
            <select
              id="filter-status"
              v-model="statusFilter"
              @change="onFilterChanged"
              class="input-glass px-2.5 py-1.5 text-xs"
            >
              <option value="">All statuses</option>
              <option value="OPEN">Open</option>
              <option value="IN_REVIEW">In Review</option>
              <option value="REMEDIATED">Remediated</option>
              <option value="REOPENED">Reopened</option>
              <option value="FALSE_POSITIVE">False Positive</option>
              <option value="ACCEPTED_RISK">Accepted Risk</option>
            </select>

            <label for="filter-scope" class="sr-only">Filter by scope</label>
            <select
              id="filter-scope"
              v-model="quarantineFilter"
              @change="onFilterChanged"
              class="input-glass px-2.5 py-1.5 text-xs"
            >
              <option value="ALL">All scopes</option>
              <option value="IN_SCOPE">In Scope only</option>
              <option value="QUARANTINED">Out of Scope only</option>
            </select>

            <button
              v-if="hasActiveFilters"
              type="button"
              @click="resetFilters"
              class="btn-glass px-2.5 py-1.5 text-xs"
            >
              Reset filters
            </button>
          </div>

          <div class="relative flex-1 min-w-[220px] max-w-sm">
            <Search
              class="h-3.5 w-3.5 text-[#8A8D96] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
              aria-hidden="true"
            />
            <label for="triage-search" class="sr-only">Search findings or target host</label>
            <input
              id="triage-search"
              v-model.trim="searchInput"
              type="text"
              placeholder="Search findings or target host..."
              class="input-glass w-full pl-8 pr-3 py-1.5 text-xs"
            />
          </div>
        </div>

        <!-- Bulk Selection Action Bar -->
        <div
          v-if="selectedIds.length > 0 && canTriage"
          class="border border-white/[0.24] bg-[#0E0E13] px-4 py-3 flex flex-wrap items-center justify-between gap-3 text-xs"
        >
          <div class="font-medium text-[#F5F5F3] tabular-nums">
            {{ selectedIds.length }} findings selected on this page
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <button
              type="button"
              :disabled="bulkBusy"
              @click="handleBulkCurate(true)"
              class="btn-platinum px-3 py-1.5 text-xs disabled:opacity-50"
            >
              Include in report
            </button>
            <button
              type="button"
              :disabled="bulkBusy"
              @click="handleBulkCurate(false)"
              class="btn-glass px-3 py-1.5 text-xs disabled:opacity-50"
            >
              Remove from report
            </button>
            <select
              :disabled="bulkBusy"
              aria-label="Bulk status update"
              @change="handleBulkStatusChange"
              class="input-glass px-2.5 py-1.5 text-xs"
            >
              <option value="">Change status...</option>
              <option value="OPEN">Open</option>
              <option value="IN_REVIEW">In Review</option>
              <option value="REMEDIATED">Remediated</option>
              <option value="REOPENED">Reopened</option>
              <option value="FALSE_POSITIVE">False Positive</option>
              <option value="ACCEPTED_RISK">Accepted Risk</option>
            </select>
            <button
              type="button"
              @click="selectedIds = []"
              class="text-[#8A8D96] hover:text-[#F5F5F3] px-2 py-1 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>

        <!-- Triage Table Ledger -->
        <div class="border border-white/[0.11] bg-[#08080B] overflow-hidden">
          <SkeletonBlock v-if="loading" variant="table-row" :count="5" />

          <div v-else-if="findings.length === 0" class="p-8">
            <EmptyState
              :icon="Search"
              title="No findings found"
              :description="
                hasActiveFilters
                  ? 'No findings match your current filters. Reset filters to view all results.'
                  : 'No scan results have been imported into this project yet.'
              "
              :action-label="hasActiveFilters ? 'Reset filters' : canTriage ? 'Add finding manually' : ''"
              @action="hasActiveFilters ? resetFilters() : openManualModal()"
            />
          </div>

          <div v-else class="overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead
                class="bg-[#050507] border-b border-white/[0.1] font-mono uppercase text-[10px] tracking-wider text-[#8A8D96]"
              >
                <tr>
                  <th v-if="canTriage" class="py-3 px-3 w-10 text-center">
                    <input
                      type="checkbox"
                      aria-label="Select all findings on this page"
                      :checked="allPageSelected"
                      @change="toggleSelectAllPage"
                      class="bg-[#050507] border-white/30 text-[#F5F5F3]"
                    />
                  </th>
                  <th class="py-3 px-3 w-16 text-center" title="Include in PDF report">Report</th>
                  <th class="py-3 px-4">Finding &amp; Target</th>
                  <th class="py-3 px-3 w-36">Severity</th>
                  <th class="py-3 px-3 w-40">Status</th>
                  <th class="py-3 px-3 w-32 text-center">Scope</th>
                  <th class="py-3 px-3 w-28 text-center">Details</th>
                </tr>
              </thead>

              <tbody class="divide-y divide-white/[0.08]">
                <tr
                  v-for="f in findings"
                  :key="f.id"
                  :class="[
                    'transition-colors',
                    drawerFinding?.id === f.id
                      ? 'bg-white/[0.06]'
                      : 'hover:bg-white/[0.025]',
                  ]"
                >
                  <td v-if="canTriage" class="py-3 px-3 text-center">
                    <input
                      type="checkbox"
                      :aria-label="`Select ${f.title}`"
                      :checked="selectedIds.includes(f.id)"
                      @change="toggleRowSelect(f.id)"
                      class="bg-[#050507] border-white/30 text-[#F5F5F3]"
                    />
                  </td>

                  <td class="py-3 px-3 text-center">
                    <input
                      type="checkbox"
                      :aria-label="`Include ${f.title} in PDF report`"
                      :checked="f.is_curated_for_report"
                      :disabled="!canTriage || f.status === 'FALSE_POSITIVE' || f.is_quarantined"
                      @change="toggleCuration(f, $event)"
                      class="bg-[#050507] border-white/30 text-[#F5F5F3] cursor-pointer disabled:opacity-35 disabled:cursor-not-allowed"
                      :title="curationDisabledHint(f)"
                    />
                  </td>

                  <td class="py-3 px-4 max-w-md">
                    <button
                      type="button"
                      @click="openFindingDrawer(f)"
                      class="text-left group block w-full"
                    >
                      <div class="font-medium text-[#F5F5F3] group-hover:underline underline-offset-4">
                        {{ f.title }}
                      </div>
                      <div
                        class="text-[11px] text-[#8A8D96] font-mono flex flex-wrap items-center gap-1.5 mt-0.5"
                      >
                        <span>{{ f.cwe_id }}</span>
                        <span>·</span>
                        <span>{{ f.source_tool }}</span>
                        <span>·</span>
                        <span class="truncate">
                          {{ f.target_host }}{{ f.target_port ? `:${f.target_port}` : '' }}{{ f.endpoint_path }}
                        </span>
                      </div>
                    </button>
                  </td>

                  <td class="py-3 px-3">
                    <SeverityBadge :severity="f.severity" :score="f.cvss_score" />
                  </td>

                  <td class="py-3 px-3">
                    <select
                      :aria-label="`Change status for ${f.title}`"
                      :value="f.status"
                      :disabled="!canTriage"
                      @change="handleStatusChange(f, $event)"
                      class="input-glass px-2 py-1 text-xs w-full disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                      <option value="OPEN">Open</option>
                      <option value="IN_REVIEW">In Review</option>
                      <option value="REMEDIATED">Remediated</option>
                      <option value="REOPENED">Reopened</option>
                      <option value="FALSE_POSITIVE">False Positive</option>
                      <option value="ACCEPTED_RISK">Accepted Risk</option>
                    </select>
                  </td>

                  <td class="py-3 px-3 text-center">
                    <div class="flex flex-col items-center gap-1">
                      <StatusBadge :status="f.is_quarantined ? 'QUARANTINED' : 'IN-SCOPE'" />
                      <button
                        v-if="f.is_quarantined && isManager"
                        type="button"
                        @click="promptUnquarantine(f)"
                        class="text-[11px] font-medium text-amber-300 hover:underline"
                      >
                        Approve scope
                      </button>
                    </div>
                  </td>

                  <td class="py-3 px-3 text-center">
                    <button
                      type="button"
                      @click="openFindingDrawer(f)"
                      class="btn-glass px-2.5 py-1.5 text-xs"
                      title="Inspect finding details and technical proof"
                    >
                      <Lock v-if="canTriage" class="h-3 w-3 text-emerald-400" aria-hidden="true" />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pagination Footer -->
          <div
            class="flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-t border-white/[0.1] bg-[#050507] text-xs text-[#8A8D96] tabular-nums"
          >
            <span>{{ paginationRangeLabel }}</span>
            <div class="flex items-center gap-2">
              <button
                type="button"
                :disabled="offset === 0"
                @click="prevPage"
                class="btn-glass px-3 py-1 text-xs disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                type="button"
                :disabled="offset + limit >= totalCount"
                @click="nextPage"
                class="btn-glass px-3 py-1 text-xs disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Slide-Over Finding Detail & Evidence Drawer -->
    <Teleport to="body">
      <Transition name="vf-fade">
        <div
          v-if="drawerFinding"
          class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex justify-end"
          @click.self="closeFindingDrawer"
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="drawer-finding-title"
            class="w-full max-w-2xl bg-[#08080B] border-l border-white/[0.14] h-full flex flex-col shadow-2xl overflow-hidden"
          >
            <!-- Drawer Header -->
            <div class="px-6 py-4 border-b border-white/[0.1] bg-[#050507] flex items-start justify-between gap-4 shrink-0">
              <div class="space-y-1.5 min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <SeverityBadge :severity="drawerFinding.severity" :score="drawerFinding.cvss_score" />
                  <StatusBadge :status="drawerFinding.status" />
                  <StatusBadge v-if="drawerFinding.is_quarantined" status="QUARANTINED" />
                  <span class="text-xs font-mono text-[#8A8D96] tabular-nums">
                    v{{ drawerFinding.version }}
                  </span>
                </div>
                <h2 id="drawer-finding-title" class="text-base font-display font-semibold text-[#F5F5F3]">
                  {{ drawerFinding.title }}
                </h2>
                <p class="text-xs font-mono text-[#8A8D96] truncate">
                  {{ drawerFinding.target_host }}{{ drawerFinding.target_port ? `:${drawerFinding.target_port}` : '' }}{{ drawerFinding.endpoint_path }}
                </p>
              </div>
              <button
                type="button"
                @click="closeFindingDrawer"
                class="p-2 text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.06] transition-colors"
                aria-label="Close finding details"
              >
                <X class="h-4 w-4" />
              </button>
            </div>

            <!-- Drawer Body -->
            <div class="flex-1 overflow-y-auto p-6 space-y-6">
              <!-- Metadata + Radar Grid (Flat Hairline Spec Rows) -->
              <div class="grid grid-cols-1 md:grid-cols-12 gap-5 items-center">
                <div class="md:col-span-5 p-3 bg-[#050507] border border-white/[0.1] flex justify-center">
                  <CvssRadarChart
                    :metrics="parseCvssVector(drawerFinding.cvss_vector)"
                    :score="drawerFinding.cvss_score"
                    :severity="drawerFinding.severity"
                    :size="190"
                  />
                </div>
                <dl class="md:col-span-7 border-y border-white/[0.1] divide-y divide-white/[0.08] text-xs">
                  <div class="py-2.5 flex justify-between gap-4">
                    <dt class="text-[#8A8D96]">Category &amp; Source</dt>
                    <dd class="text-[#F5F5F3] font-mono font-semibold text-right">
                      {{ drawerFinding.cwe_id }} · {{ drawerFinding.source_tool }}
                    </dd>
                  </div>
                  <div class="py-2.5 flex justify-between gap-4">
                    <dt class="text-[#8A8D96]">Protocol &amp; Port</dt>
                    <dd class="text-[#F5F5F3] font-mono font-semibold uppercase text-right">
                      {{ drawerFinding.protocol }} / {{ drawerFinding.target_port ?? '—' }}
                    </dd>
                  </div>
                  <div class="py-2.5 space-y-1">
                    <dt class="text-[#8A8D96]">CVSS Vector</dt>
                    <dd class="text-[#D4D4D8] font-mono text-[11px] break-all">
                      {{ drawerFinding.cvss_vector || 'Not set' }}
                    </dd>
                  </div>
                </dl>
              </div>

              <!-- Quick Triage Controls inside Drawer -->
              <div
                v-if="canTriage"
                class="py-3.5 border-y border-white/[0.1] flex flex-wrap items-center justify-between gap-3"
              >
                <label class="flex items-center gap-2 text-xs text-[#F5F5F3] cursor-pointer">
                  <input
                    type="checkbox"
                    :checked="drawerFinding.is_curated_for_report"
                    :disabled="drawerFinding.status === 'FALSE_POSITIVE' || drawerFinding.is_quarantined"
                    @change="toggleCuration(drawerFinding, $event)"
                    class="bg-[#050507] border-white/30 text-[#F5F5F3] disabled:opacity-40"
                  />
                  <span>Include in PDF report</span>
                </label>

                <button
                  v-if="drawerFinding.is_quarantined && isManager"
                  type="button"
                  @click="promptUnquarantine(drawerFinding)"
                  class="btn-glass px-3 py-1.5 text-xs text-amber-300 border-amber-400/35"
                >
                  Approve into scope
                </button>
              </div>

              <!-- Protected Technical Evidence Section -->
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <h3 class="text-sm font-display font-semibold text-[#F5F5F3] flex items-center gap-2">
                    <Key class="h-4 w-4 text-emerald-400" aria-hidden="true" />
                    <span>Protected Technical Evidence</span>
                  </h3>
                  <button
                    v-if="pocData?.raw_evidence"
                    type="button"
                    @click="copyText(pocData.raw_evidence, 'Technical proof')"
                    class="btn-glass px-2.5 py-1 text-xs"
                  >
                    <Copy class="h-3 w-3" />
                    <span>Copy proof</span>
                  </button>
                </div>

                <div
                  v-if="!canTriage"
                  class="p-4 bg-[#050507] border border-white/[0.1] text-xs text-[#D4D4D8]"
                >
                  Technical proof decryption is restricted to Workspace Managers and Pentesters.
                </div>

                <SkeletonBlock v-else-if="pocLoading" variant="text" :count="4" />

                <template v-else-if="pocData">
                  <div class="p-3.5 bg-[#050507] border border-white/[0.1] space-y-2 text-xs">
                    <div class="flex justify-between font-mono text-[11px] text-[#8A8D96]">
                      <span>Encrypted at rest (Key v{{ pocData.key_version }})</span>
                      <span class="text-emerald-400">Access logged</span>
                    </div>
                    <pre class="font-mono text-[#F5F5F3] overflow-x-auto whitespace-pre-wrap break-all max-h-60">{{
                      pocData.raw_evidence || '(No raw proof attached)'
                    }}</pre>
                  </div>

                  <div v-if="pocData.reproduction_steps.length > 0" class="space-y-1.5 text-xs">
                    <span class="font-mono text-[11px] uppercase tracking-wider text-[#8A8D96] block">Reproduction Steps</span>
                    <ol
                      class="list-decimal list-inside space-y-1.5 text-[#D4D4D8] bg-[#050507] p-3.5 border border-white/[0.1]"
                    >
                      <li v-for="(step, idx) in pocData.reproduction_steps" :key="idx">{{ step }}</li>
                    </ol>
                  </div>

                  <!-- Drag & Drop Attachment Upload + Inline Thumbnail Gallery -->
                  <div class="space-y-3 pt-2">
                    <span class="font-mono text-[11px] uppercase tracking-wider text-[#8A8D96] block">
                      Evidence Screenshots ({{ pocData.attachment_file_urls.length }})
                    </span>

                    <label
                      v-if="canTriage"
                      @dragover.prevent="dragOverUpload = true"
                      @dragleave.prevent="dragOverUpload = false"
                      @drop.prevent="handleDropAttachment"
                      :class="[
                        'flex flex-col items-center justify-center gap-1.5 p-4 border border-dashed transition-colors cursor-pointer text-center',
                        dragOverUpload
                          ? 'border-[#F5F5F3] bg-white/[0.06] text-[#F5F5F3]'
                          : 'border-white/[0.16] bg-[#050507] text-[#D4D4D8] hover:border-white/30',
                      ]"
                    >
                      <Upload class="h-5 w-5 text-[#F5F5F3]" aria-hidden="true" />
                      <span class="text-xs font-medium">
                        {{
                          uploadingAttachment
                            ? 'Uploading screenshot...'
                            : 'Drag & drop PNG or JPEG here, or click to upload (Max 5 MB)'
                        }}
                      </span>
                      <input
                        type="file"
                        accept="image/png,image/jpeg"
                        class="hidden"
                        :disabled="uploadingAttachment"
                        @change="handlePoCAttachmentUpload"
                      />
                    </label>

                    <div
                      v-if="pocData.attachment_file_urls.length > 0"
                      class="grid grid-cols-1 sm:grid-cols-2 gap-3"
                    >
                      <div
                        v-for="(url, idx) in pocData.attachment_file_urls"
                        :key="idx"
                        class="border border-white/[0.1] bg-[#050507] overflow-hidden group"
                      >
                        <button
                          type="button"
                          @click="lightboxUrl = url"
                          class="w-full h-32 bg-black flex items-center justify-center overflow-hidden"
                        >
                          <img
                            :src="url"
                            :alt="`Evidence screenshot ${idx + 1}`"
                            class="w-full h-full object-cover group-hover:scale-105 transition-transform"
                          />
                        </button>
                        <div class="px-3 py-2 flex items-center justify-between text-xs border-t border-white/[0.08]">
                          <span class="text-[#D4D4D8]">Screenshot #{{ idx + 1 }}</span>
                          <a
                            :href="url"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="text-[#F5F5F3] underline underline-offset-4 text-xs"
                          >
                            Open tab ↗
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Lightbox Modal for Screenshot Preview -->
    <BaseModal
      :open="Boolean(lightboxUrl)"
      title="Evidence Screenshot Preview"
      max-width="2xl"
      @close="lightboxUrl = null"
    >
      <div v-if="lightboxUrl" class="flex justify-center bg-[#050507] border border-white/[0.1] p-2">
        <img :src="lightboxUrl" alt="Full-size evidence screenshot" class="max-h-[70vh] object-contain" />
      </div>
    </BaseModal>

    <!-- Unquarantine Confirmation Dialog -->
    <ConfirmDialog
      :open="Boolean(unquarantineTarget)"
      title="Allow Out-of-Scope Finding?"
      :message="`Finding '${unquarantineTarget?.title || ''}' matched a host outside this project's authorized targets. Approving it will include it as an in-scope candidate for PDF reports.`"
      confirm-text="Approve & Include"
      variant="warning"
      :loading="unquarantining"
      @confirm="confirmUnquarantine"
      @cancel="unquarantineTarget = null"
    />

    <!-- Manual Finding Modal (isolated manualMetrics + CvssRadarChart) -->
    <BaseModal
      :open="showManualModal"
      title="Add Manual Finding"
      subtitle="Technical proof is encrypted before storage in this project."
      max-width="xl"
      @close="showManualModal = false"
    >
      <form id="manual-finding-form" @submit.prevent="handleCreateManual" class="space-y-4 text-xs">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="space-y-1.5 sm:col-span-2">
            <label for="manual-title" class="font-medium text-[#D4D4D8] block">Finding title</label>
            <input
              id="manual-title"
              v-model.trim="manualForm.title"
              type="text"
              required
              placeholder="Broken object-level access on profile endpoint"
              class="input-glass w-full px-3 py-2 text-xs"
            />
          </div>

          <div class="space-y-1.5">
            <label for="manual-cwe" class="font-medium text-[#D4D4D8] block">Category (CWE)</label>
            <select
              id="manual-cwe"
              v-model="manualForm.cwe_id"
              class="input-glass w-full px-2.5 py-2 text-xs"
            >
              <option v-for="cwe in CWE_OPTIONS" :key="cwe.id" :value="cwe.id">
                {{ cwe.label }}
              </option>
            </select>
          </div>

          <div class="space-y-1.5">
            <label for="manual-protocol" class="font-medium text-[#D4D4D8] block">Protocol</label>
            <select
              id="manual-protocol"
              v-model="manualForm.protocol"
              class="input-glass w-full px-2.5 py-2 text-xs font-mono"
            >
              <option value="https">https</option>
              <option value="http">http</option>
              <option value="tcp">tcp</option>
              <option value="udp">udp</option>
              <option value="other">other</option>
            </select>
          </div>

          <div class="space-y-1.5">
            <label for="manual-host" class="font-medium text-[#D4D4D8] block">Target host</label>
            <input
              id="manual-host"
              v-model.trim="manualForm.target_host"
              type="text"
              required
              placeholder="api.example.com"
              class="input-glass w-full px-3 py-2 font-mono text-xs"
            />
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div class="space-y-1.5">
              <label for="manual-port" class="font-medium text-[#D4D4D8] block">Port (optional)</label>
              <input
                id="manual-port"
                v-model.number="manualForm.target_port"
                type="number"
                min="0"
                max="65535"
                placeholder="443"
                class="input-glass w-full px-3 py-2 font-mono text-xs"
              />
            </div>
            <div class="space-y-1.5">
              <label for="manual-endpoint" class="font-medium text-[#D4D4D8] block">Endpoint path</label>
              <input
                id="manual-endpoint"
                v-model.trim="manualForm.endpoint_path"
                type="text"
                placeholder="/api/v1/profile/12"
                class="input-glass w-full px-3 py-2 font-mono text-xs"
              />
            </div>
          </div>
        </div>

        <!-- Embedded CVSS v3.1 Builder + Radar -->
        <div class="p-4 bg-[#050507] border border-white/[0.1] space-y-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <span class="font-semibold text-[#F5F5F3]">CVSS v3.1 Score Builder</span>
            <SeverityBadge :severity="manualCvssResult.severity" :score="manualCvssResult.score" />
          </div>

          <div class="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
            <div class="md:col-span-4 flex justify-center">
              <CvssRadarChart
                :metrics="manualMetrics"
                :score="manualCvssResult.score"
                :severity="manualCvssResult.severity"
                :size="175"
              />
            </div>
            <div class="md:col-span-8 grid grid-cols-2 gap-2 text-xs">
              <div v-for="def in metricDefsList" :key="def.key" class="space-y-1">
                <label :for="`manual-cvss-${def.key}`" class="text-xs text-[#8A8D96] block truncate">
                  {{ def.name }}
                </label>
                <select
                  :id="`manual-cvss-${def.key}`"
                  v-model="manualMetrics[def.key]"
                  class="input-glass w-full px-2 py-1 text-xs"
                >
                  <option v-for="opt in def.options" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </select>
              </div>
            </div>
          </div>
          <div class="text-[11px] font-mono text-[#8A8D96] break-all">
            Vector: <span class="text-[#F5F5F3]">{{ manualCvssResult.vector }}</span>
          </div>
        </div>

        <div class="space-y-1.5">
          <label for="manual-evidence" class="font-medium text-[#D4D4D8] block">
            Technical proof (encrypted at rest)
          </label>
          <textarea
            id="manual-evidence"
            v-model="manualForm.raw_evidence"
            rows="3"
            required
            placeholder="HTTP request/response or reproduction payload..."
            class="input-glass w-full p-3 font-mono text-xs"
          ></textarea>
        </div>

        <div class="space-y-1.5">
          <label for="manual-steps" class="font-medium text-[#D4D4D8] block">
            Reproduction steps (one step per line)
          </label>
          <textarea
            id="manual-steps"
            v-model="manualForm.stepsRaw"
            rows="2"
            placeholder="1. Sign in as User A&#10;2. Replace user_id with User B's identifier"
            class="input-glass w-full p-3 font-mono text-xs"
          ></textarea>
        </div>
      </form>

      <template #footer>
        <button
          type="button"
          @click="showManualModal = false"
          class="btn-glass px-4 py-2 text-xs"
        >
          Cancel
        </button>
        <button
          type="submit"
          form="manual-finding-form"
          :disabled="submittingManual"
          class="btn-platinum px-4 py-2 text-xs disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Loader2 v-if="submittingManual" class="h-3.5 w-3.5 animate-spin" />
          <span>{{ submittingManual ? 'Saving...' : 'Save finding' }}</span>
        </button>
      </template>
    </BaseModal>

    <!-- Standalone FIRST CVSS v3.1 Calculator Modal (isolated calcMetrics) -->
    <BaseModal
      :open="showCvssModal"
      title="CVSS v3.1 Calculator"
      subtitle="Simulate risk scores and severity ratings interactively."
      max-width="xl"
      @close="showCvssModal = false"
    >
      <div class="space-y-5">
        <div class="grid grid-cols-1 md:grid-cols-12 gap-5 items-center">
          <div class="md:col-span-5 flex flex-col items-center justify-center p-4 bg-[#050507] border border-white/[0.1]">
            <CvssRadarChart
              :metrics="calcMetrics"
              :score="calcCvssResult.score"
              :severity="calcCvssResult.severity"
              :size="200"
            />
            <div class="mt-2">
              <SeverityBadge :severity="calcCvssResult.severity" :score="calcCvssResult.score" size="md" />
            </div>
          </div>

          <div class="md:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div v-for="def in metricDefsList" :key="def.key" class="space-y-1">
              <label :for="`calc-cvss-${def.key}`" class="text-xs text-[#8A8D96] block">
                {{ def.name }}
              </label>
              <select
                :id="`calc-cvss-${def.key}`"
                v-model="calcMetrics[def.key]"
                class="input-glass w-full px-2.5 py-1.5 text-xs"
              >
                <option v-for="opt in def.options" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <div class="p-3.5 bg-[#050507] border border-white/[0.1] font-mono text-xs flex flex-wrap items-center justify-between gap-2">
          <span class="text-[#D4D4D8] break-all">{{ calcCvssResult.vector }}</span>
          <button
            type="button"
            @click="copyText(calcCvssResult.vector, 'CVSS Vector')"
            class="font-sans text-[#F5F5F3] underline underline-offset-4 shrink-0"
          >
            Copy vector
          </button>
        </div>
      </div>

      <template #footer>
        <button
          v-if="canTriage"
          type="button"
          @click="applyCvssToManual"
          class="btn-glass px-4 py-2 text-xs"
        >
          Use in manual finding
        </button>
        <button
          type="button"
          @click="showCvssModal = false"
          class="btn-platinum px-4 py-2 text-xs"
        >
          Close
        </button>
      </template>
    </BaseModal>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  ArrowRight,
  Calculator,
  Copy,
  FolderGit2,
  Key,
  Loader2,
  Lock,
  Plus,
  Search,
  Upload,
  X,
} from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import CvssRadarChart from '@/components/ui/CvssRadarChart.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import SeverityBadge from '@/components/ui/SeverityBadge.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import {
  api,
  ApiError,
  type Finding,
  type FindingPoC,
  type FindingStatus,
  type FindingSummaryMetrics,
  type Protocol,
  type Severity,
} from '@/services/api'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'
import {
  CWE_OPTIONS,
  CVSS_METRIC_DEFS,
  DEFAULT_CVSS_METRICS,
  computeCvss31,
  parseCvssVector,
  type CvssMetrics,
} from '@/utils/cvss'
import { readFileAsBase64 } from '@/utils/files'

const route = useRoute()
const activeProject = session.activeProject
const isManager = computed(() => session.activeRole.value === 'MANAGER')
const canTriage = computed(() => session.activeRole.value !== 'VIEWER')

const findings = ref<Finding[]>([])
const summary = ref<FindingSummaryMetrics>({
  total: 0,
  curated: 0,
  quarantined: 0,
  by_severity: {},
  by_status: {},
})
const totalCount = ref(0)
const limit = 25
const offset = ref(0)
const loading = ref(false)
const bulkBusy = ref(false)
const selectedIds = ref<string[]>([])

const initialSeverity =
  typeof route.query.severity === 'string' &&
  ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].includes(route.query.severity)
    ? (route.query.severity as Severity)
    : ''
const initialStatus =
  typeof route.query.status === 'string' &&
  ['OPEN', 'IN_REVIEW', 'REMEDIATED', 'REOPENED', 'FALSE_POSITIVE', 'ACCEPTED_RISK'].includes(
    route.query.status
  )
    ? (route.query.status as FindingStatus)
    : ''

const severityFilter = ref<Severity | ''>(initialSeverity)
const statusFilter = ref<FindingStatus | ''>(initialStatus)
const pendingQueryFindingId = ref(
  typeof route.query.finding === 'string' ? route.query.finding : ''
)
const quarantineFilter = ref<'ALL' | 'IN_SCOPE' | 'QUARANTINED'>('ALL')
const searchInput = ref('')
const debouncedSearch = ref('')

let searchTimer: number | undefined
watch(searchInput, (val) => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(() => {
    debouncedSearch.value = val
    offset.value = 0
  }, 300)
})

const drawerFinding = ref<Finding | null>(null)
const pocData = ref<FindingPoC | null>(null)
const pocLoading = ref(false)
const uploadingAttachment = ref(false)
const dragOverUpload = ref(false)
const lightboxUrl = ref<string | null>(null)

const unquarantineTarget = ref<Finding | null>(null)
const unquarantining = ref(false)

const showCvssModal = ref(false)
const showManualModal = ref(false)
const submittingManual = ref(false)

const metricDefsList = Object.values(CVSS_METRIC_DEFS)
const calcMetrics = reactive<CvssMetrics>({ ...DEFAULT_CVSS_METRICS })
const manualMetrics = reactive<CvssMetrics>({ ...DEFAULT_CVSS_METRICS })
const calcCvssResult = computed(() => computeCvss31(calcMetrics))
const manualCvssResult = computed(() => computeCvss31(manualMetrics))

const manualForm = ref({
  title: '',
  cwe_id: 'CWE-89',
  protocol: 'https' as Protocol,
  target_host: '',
  target_port: undefined as number | undefined,
  endpoint_path: '',
  raw_evidence: '',
  stepsRaw: '',
})

const hasActiveFilters = computed(
  () =>
    Boolean(severityFilter.value) ||
    Boolean(statusFilter.value) ||
    quarantineFilter.value !== 'ALL' ||
    Boolean(debouncedSearch.value)
)

const paginationRangeLabel = computed(() => {
  if (totalCount.value === 0) return '0 findings'
  const start = offset.value + 1
  const end = Math.min(offset.value + findings.value.length, totalCount.value)
  return `Showing ${start}–${end} of ${totalCount.value} findings`
})

const allPageSelected = computed(
  () =>
    findings.value.length > 0 && findings.value.every((f) => selectedIds.value.includes(f.id))
)

const curationDisabledHint = (f: Finding): string => {
  if (!canTriage.value) return 'Restricted to Managers and Pentesters'
  if (f.is_quarantined) return 'Approve finding into scope first'
  if (f.status === 'FALSE_POSITIVE') return 'False Positive findings cannot be included in reports'
  return 'Include in PDF report'
}

const onFilterChanged = () => {
  offset.value = 0
}

const resetFilters = () => {
  severityFilter.value = ''
  statusFilter.value = ''
  quarantineFilter.value = 'ALL'
  searchInput.value = ''
  debouncedSearch.value = ''
  offset.value = 0
}

let triageFetchSeq = 0
let triagePoCSeq = 0

async function fetchFindings(): Promise<void> {
  const seq = ++triageFetchSeq
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  if (!wId || !pId) {
    findings.value = []
    totalCount.value = 0
    summary.value = { total: 0, curated: 0, quarantined: 0, by_severity: {}, by_status: {} }
    drawerFinding.value = null
    pocData.value = null
    return
  }

  loading.value = true
  try {
    const isQuarantinedParam =
      quarantineFilter.value === 'ALL'
        ? null
        : quarantineFilter.value === 'QUARANTINED'

    const res = await api.findings.list(wId, pId, {
      severity: severityFilter.value || undefined,
      status: statusFilter.value || undefined,
      is_quarantined: isQuarantinedParam,
      search: debouncedSearch.value || undefined,
      limit,
      offset: offset.value,
    })
    if (
      seq !== triageFetchSeq ||
      session.state.activeWorkspaceId !== wId ||
      session.state.activeProjectId !== pId
    ) {
      return
    }
    findings.value = res.items
    totalCount.value = res.total
    summary.value = res.summary
    selectedIds.value = selectedIds.value.filter((id) => res.items.some((i) => i.id === id))
    if (drawerFinding.value) {
      drawerFinding.value =
        res.items.find((i) => i.id === drawerFinding.value?.id) ?? drawerFinding.value
    }
    if (pendingQueryFindingId.value) {
      const targetId = pendingQueryFindingId.value
      pendingQueryFindingId.value = ''
      const matched = res.items.find((i) => i.id === targetId)
      if (matched) {
        void openFindingDrawer(matched)
      }
    }
  } catch (err: unknown) {
    if (seq === triageFetchSeq) {
      toast.error(err instanceof Error ? err.message : 'Unable to load project findings.')
    }
  } finally {
    if (seq === triageFetchSeq) {
      loading.value = false
    }
  }
}

watch(
  [
    () => session.state.activeWorkspaceId,
    () => session.state.activeProjectId,
    severityFilter,
    statusFilter,
    quarantineFilter,
    debouncedSearch,
    offset,
  ],
  () => {
    void fetchFindings()
  },
  { immediate: true }
)

const prevPage = () => {
  offset.value = Math.max(0, offset.value - limit)
}
const nextPage = () => {
  if (offset.value + limit < totalCount.value) {
    offset.value += limit
  }
}

const toggleRowSelect = (id: string) => {
  if (selectedIds.value.includes(id)) {
    selectedIds.value = selectedIds.value.filter((x) => x !== id)
  } else {
    selectedIds.value = [...selectedIds.value, id]
  }
}

const toggleSelectAllPage = () => {
  if (allPageSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = findings.value.map((f) => f.id)
  }
}

const handleBulkCurate = async (curated: boolean) => {
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  if (!wId || !pId) return

  const targets = findings.value.filter(
    (f) =>
      selectedIds.value.includes(f.id) &&
      !f.is_quarantined &&
      f.status !== 'FALSE_POSITIVE'
  )
  if (targets.length === 0) {
    toast.warning('No eligible findings selected (must be in scope and not False Positive).')
    return
  }

  bulkBusy.value = true
  try {
    const results = await Promise.allSettled(
      targets.map((f) =>
        api.findings.updateCuration(wId, pId, f.id, { is_curated_for_report: curated })
      )
    )
    const okCount = results.filter((r) => r.status === 'fulfilled').length
    toast.success(
      `${okCount} findings ${curated ? 'included in' : 'removed from'} the PDF report.`
    )
    selectedIds.value = []
    await fetchFindings()
    void session.refreshProjectProgress()
  } finally {
    bulkBusy.value = false
  }
}

const handleBulkStatusChange = async (event: Event) => {
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  const selectEl = event.target as HTMLSelectElement
  const nextStatus = selectEl.value as FindingStatus | ''
  selectEl.value = ''
  if (!wId || !pId || !nextStatus) return

  const targets = findings.value.filter((f) => selectedIds.value.includes(f.id))
  if (targets.length === 0) return

  bulkBusy.value = true
  try {
    const results = await Promise.allSettled(
      targets.map((f) => api.findings.updateStatus(wId, pId, f.id, nextStatus, f.version))
    )
    const okCount = results.filter((r) => r.status === 'fulfilled').length
    const failCount = results.length - okCount
    if (okCount > 0) {
      toast.success(`${okCount} findings updated.`)
    }
    if (failCount > 0) {
      toast.warning(`${failCount} findings could not be updated due to version conflict.`)
    }
    selectedIds.value = []
    await fetchFindings()
    void session.refreshProjectProgress()
  } finally {
    bulkBusy.value = false
  }
}

const handleStatusChange = async (f: Finding, event: Event) => {
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  if (!wId || !pId) return

  const selectEl = event.target as HTMLSelectElement
  const nextStatus = selectEl.value as FindingStatus
  try {
    const updated = await api.findings.updateStatus(wId, pId, f.id, nextStatus, f.version)
    f.status = updated.status
    f.version = updated.version
    f.is_curated_for_report = updated.is_curated_for_report
    toast.success('Finding status updated.')
    await fetchFindings()
    void session.refreshProjectProgress()
  } catch (err: unknown) {
    selectEl.value = f.status
    if (err instanceof ApiError && err.status === 409) {
      toast.warning('Version conflict: this finding was updated elsewhere. Refreshing...')
      await fetchFindings()
      return
    }
    toast.error(err instanceof Error ? err.message : 'Unable to update finding status.')
  }
}

const toggleCuration = async (f: Finding, event: Event) => {
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  if (!wId || !pId) return

  const checkbox = event.target as HTMLInputElement
  const desired = checkbox.checked
  try {
    const updated = await api.findings.updateCuration(wId, pId, f.id, {
      is_curated_for_report: desired,
    })
    f.is_curated_for_report = updated.is_curated_for_report
    await fetchFindings()
    void session.refreshProjectProgress()
  } catch (err: unknown) {
    checkbox.checked = f.is_curated_for_report
    toast.error(err instanceof Error ? err.message : 'Unable to update report selection.')
  }
}

const promptUnquarantine = (f: Finding) => {
  unquarantineTarget.value = f
}

const confirmUnquarantine = async () => {
  const f = unquarantineTarget.value
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  if (!f || !wId || !pId) return

  unquarantining.value = true
  try {
    await api.findings.updateCuration(wId, pId, f.id, {
      is_curated_for_report: true,
      unquarantine: true,
    })
    unquarantineTarget.value = null
    toast.success('Finding approved into scope and selected for the report.')
    await fetchFindings()
    void session.refreshProjectProgress()
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to approve finding into scope.')
  } finally {
    unquarantining.value = false
  }
}

const openFindingDrawer = async (f: Finding) => {
  const pocSeq = ++triagePoCSeq
  drawerFinding.value = f
  pocData.value = null
  if (!canTriage.value) return

  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  if (!wId || !pId) return

  pocLoading.value = true
  try {
    const res = await api.findings.getPoC(wId, pId, f.id)
    if (
      pocSeq !== triagePoCSeq ||
      drawerFinding.value?.id !== f.id ||
      session.state.activeWorkspaceId !== wId ||
      session.state.activeProjectId !== pId
    ) {
      return
    }
    pocData.value = res
  } catch (err: unknown) {
    if (pocSeq === triagePoCSeq && drawerFinding.value?.id === f.id) {
      toast.error(err instanceof Error ? err.message : 'Unable to load protected evidence.')
    }
  } finally {
    if (pocSeq === triagePoCSeq) {
      pocLoading.value = false
    }
  }
}

const closeFindingDrawer = () => {
  triagePoCSeq += 1
  drawerFinding.value = null
  pocData.value = null
  pocLoading.value = false
}

watch(
  () => route.query.finding,
  (val) => {
    if (typeof val === 'string' && val) {
      pendingQueryFindingId.value = val
      const matched = findings.value.find((i) => i.id === val)
      if (matched) {
        pendingQueryFindingId.value = ''
        void openFindingDrawer(matched)
      }
    }
  }
)

const onDrawerEscape = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && drawerFinding.value && !lightboxUrl.value && !unquarantineTarget.value) {
    closeFindingDrawer()
  }
}
window.addEventListener('keydown', onDrawerEscape)
onUnmounted(() => {
  window.clearTimeout(searchTimer)
  window.removeEventListener('keydown', onDrawerEscape)
})

const uploadAttachmentFile = async (file: File) => {
  if (!drawerFinding.value) return
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  if (!wId || !pId) return

  uploadingAttachment.value = true
  try {
    const encoded = await readFileAsBase64(file, {
      maxBytes: 5 * 1024 * 1024,
      allowedTypes: ['image/png', 'image/jpeg'] as const,
    })
    const res = await api.findings.uploadAttachment(wId, pId, drawerFinding.value.id, encoded)
    if (pocData.value) {
      pocData.value.attachment_file_urls = [
        ...pocData.value.attachment_file_urls,
        res.attachment_url,
      ]
    }
    toast.success('Evidence screenshot uploaded.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to upload image attachment.')
  } finally {
    uploadingAttachment.value = false
  }
}

const handlePoCAttachmentUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (file) await uploadAttachmentFile(file)
}

const handleDropAttachment = async (event: DragEvent) => {
  dragOverUpload.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) await uploadAttachmentFile(file)
}

const openManualModal = () => {
  manualForm.value = {
    title: '',
    cwe_id: 'CWE-89',
    protocol: 'https',
    target_host: activeProject.value?.target_scope[0]?.replace(/^\*\./, 'app.') || '',
    target_port: 443,
    endpoint_path: '/',
    raw_evidence: '',
    stepsRaw: '',
  }
  showManualModal.value = true
}

const applyCvssToManual = () => {
  Object.assign(manualMetrics, { ...calcMetrics })
  showCvssModal.value = false
  openManualModal()
}

const handleCreateManual = async () => {
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  if (!wId || !pId) return

  const steps = manualForm.value.stepsRaw
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean)

  submittingManual.value = true
  try {
    const portVal =
      manualForm.value.target_port !== undefined && String(manualForm.value.target_port) !== ''
        ? Number(manualForm.value.target_port)
        : null
    const res = await api.findings.createManual(wId, pId, {
      title: manualForm.value.title,
      severity: manualCvssResult.value.severity,
      cvss_vector: manualCvssResult.value.vector,
      cwe_id: manualForm.value.cwe_id,
      target_host: manualForm.value.target_host,
      target_port: portVal,
      endpoint_path: manualForm.value.endpoint_path || '',
      protocol: manualForm.value.protocol,
      proof_of_concept: {
        raw_evidence: manualForm.value.raw_evidence,
        reproduction_steps: steps,
      },
    })
    showManualModal.value = false
    if (res.is_quarantined) {
      toast.warning(
        'Finding saved as Out of Scope because the target host is outside authorized scope.'
      )
    } else {
      toast.success(`Finding saved (CVSS ${res.cvss_score}).`)
    }
    await fetchFindings()
    void session.refreshProjectProgress()
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to save manual finding.')
  } finally {
    submittingManual.value = false
  }
}

const copyText = async (text: string, label: string) => {
  try {
    await navigator.clipboard.writeText(text)
    toast.success(`${label} copied to clipboard.`)
  } catch {
    toast.info(text, label)
  }
}
</script>
