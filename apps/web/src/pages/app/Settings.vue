<template>
  <AppLayout>
    <template #header-title>
      <div>
        <h1 class="text-base font-display font-semibold text-[#F5F5F3] tracking-tight">
          {{ isSuperadmin ? 'Account Security' : 'Settings' }}
        </h1>
        <p class="text-xs text-[#8A8D96] truncate">
          {{
            isSuperadmin
              ? 'Two-factor authentication for your platform superadmin account'
              : session.state.activeWorkspace?.name || 'Workspace & account settings'
          }}
        </p>
      </div>
    </template>

    <div class="space-y-6 max-w-7xl mx-auto">
      <!-- Accessible Tabs -->
      <div
        v-if="visibleTabs.length > 1"
        role="tablist"
        aria-label="Settings categories"
        class="inline-flex flex-wrap border border-white/[0.12] divide-x divide-white/[0.1] bg-[#08080B] text-xs font-medium"
      >
        <button
          v-for="tab in visibleTabs"
          :key="tab.id"
          type="button"
          role="tab"
          :aria-selected="activeTab === tab.id"
          @click="activeTab = tab.id"
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

      <!-- TAB 1: WORKSPACE & TEAM -->
      <div v-if="activeTab === 'team'" role="tabpanel" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 border border-white/[0.11] divide-y md:divide-y-0 md:divide-x divide-white/[0.11] bg-[#08080B]">
          <!-- Rename Active Workspace (MANAGER) -->
          <div
            v-if="isManager && session.state.activeWorkspace"
            class="p-5 space-y-3"
          >
            <h2 class="text-sm font-display font-semibold text-[#F5F5F3]">Rename active workspace</h2>
            <form @submit.prevent="handleRenameWorkspace" class="flex gap-2">
              <label for="ws-rename-input" class="sr-only">New workspace name</label>
              <input
                id="ws-rename-input"
                v-model.trim="renameWorkspaceInput"
                type="text"
                required
                placeholder="Workspace name..."
                class="input-glass flex-1 min-w-0 px-3 py-2 text-xs"
              />
              <button
                type="submit"
                :disabled="renamingWs"
                class="btn-glass px-3.5 py-2 text-xs disabled:opacity-50"
              >
                {{ renamingWs ? '...' : 'Save' }}
              </button>
            </form>
          </div>

          <!-- Accept Invitation Token -->
          <div :class="['p-5 space-y-3', !(isManager && session.state.activeWorkspace) ? 'md:col-span-2' : '']">
            <h2 class="text-sm font-display font-semibold text-[#F5F5F3]">Join via invitation token</h2>
            <form @submit.prevent="handleAcceptInvitation" class="flex gap-2">
              <label for="ws-invite-token" class="sr-only">Invitation token</label>
              <input
                id="ws-invite-token"
                v-model.trim="acceptTokenInput"
                type="text"
                required
                placeholder="Paste invitation token..."
                class="input-glass flex-1 min-w-0 px-3 py-2 text-xs font-mono"
              />
              <button
                type="submit"
                :disabled="acceptingInvite"
                class="btn-glass px-4 py-2 text-xs disabled:opacity-50"
              >
                {{ acceptingInvite ? '...' : 'Join' }}
              </button>
            </form>
          </div>
        </div>

        <!-- Members List & Invite -->
        <div
          v-if="session.state.activeWorkspaceId"
          class="border border-white/[0.11] bg-[#08080B] p-6 space-y-5"
        >
          <div class="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.08] pb-3.5">
            <div>
              <h3 class="text-sm font-display font-semibold text-[#F5F5F3] tabular-nums">
                Members ({{ members.length }})
              </h3>
              <p class="text-xs text-[#8A8D96]">
                At least one Manager must remain assigned to the workspace.
              </p>
            </div>
          </div>

          <!-- Invite Form -->
          <form
            v-if="isManager"
            @submit.prevent="handleInvite"
            class="grid grid-cols-1 sm:grid-cols-12 gap-2.5 text-xs"
          >
            <label for="invite-email" class="sr-only">Teammate email</label>
            <input
              id="invite-email"
              v-model.trim="inviteEmail"
              type="email"
              required
              placeholder="teammate@company.com"
              class="input-glass sm:col-span-6 px-3 py-2 text-xs"
            />
            <label for="invite-role" class="sr-only">Teammate role</label>
            <select
              id="invite-role"
              v-model="inviteRole"
              class="input-glass sm:col-span-3 px-2.5 py-2 text-xs"
            >
              <option value="PENTESTER">Pentester</option>
              <option value="MANAGER">Manager</option>
              <option value="VIEWER">Viewer</option>
            </select>
            <button
              type="submit"
              :disabled="inviting"
              class="btn-platinum sm:col-span-3 px-3 py-2 text-xs disabled:opacity-50"
            >
              <Loader2 v-if="inviting" class="h-3.5 w-3.5 animate-spin" />
              <span>{{ inviting ? 'Sending...' : 'Send invite' }}</span>
            </button>
          </form>

          <!-- Generated Invite Banner -->
          <div
            v-if="lastInviteToken"
            class="p-3.5 bg-emerald-500/10 border border-emerald-400/25 text-xs space-y-2"
          >
            <div class="font-semibold text-emerald-300">
              Invitation sent and registration link ready:
            </div>
            <div class="flex items-center justify-between gap-2 font-mono text-[11px] bg-[#050507] border border-white/[0.1] p-2.5">
              <span class="truncate text-[#D4D4D8]">{{ lastInviteUrl }}</span>
              <button
                type="button"
                @click="copyText(lastInviteUrl, 'Invitation link')"
                class="shrink-0 font-sans text-[#F5F5F3] underline underline-offset-4 font-medium"
              >
                Copy link
              </button>
            </div>
          </div>

          <SkeletonBlock v-if="loadingTeam" variant="table-row" :count="3" />

          <div v-else class="overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead class="border-b border-white/[0.1] font-mono uppercase text-[10px] tracking-wider text-[#8A8D96]">
                <tr>
                  <th class="py-2 pr-4">Name</th>
                  <th class="py-2 px-4">Email</th>
                  <th class="py-2 px-4">Role</th>
                  <th v-if="isManager" class="py-2 pl-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/[0.08]">
                <tr v-for="m in members" :key="m.user_id">
                  <td class="py-2.5 pr-4 font-medium text-[#F5F5F3]">{{ m.full_name }}</td>
                  <td class="py-2.5 px-4 font-mono text-[#D4D4D8]">{{ m.email }}</td>
                  <td class="py-2.5 px-4">
                    <select
                      v-if="isManager"
                      :aria-label="`Change role for ${m.full_name}`"
                      :value="m.role"
                      @change="handleRoleChange(m, $event)"
                      class="input-glass px-2 py-1 text-xs"
                    >
                      <option value="MANAGER">Manager</option>
                      <option value="PENTESTER">Pentester</option>
                      <option value="VIEWER">Viewer</option>
                    </select>
                    <span v-else class="text-[#D4D4D8]">{{ formatRole(m.role) }}</span>
                  </td>
                  <td v-if="isManager" class="py-2.5 pl-4 text-right">
                    <button
                      type="button"
                      @click="removeMemberTarget = m"
                      class="text-red-400 hover:text-red-300 text-xs font-medium"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Delete Workspace Danger Zone -->
        <div
          v-if="isManager && session.state.activeWorkspace"
          class="border border-red-400/30 bg-red-500/[0.06] p-6 space-y-3"
        >
          <h3 class="text-sm font-display font-semibold text-red-300">Delete Workspace</h3>
          <p class="text-xs text-[#D4D4D8]">
            A workspace can only be deleted once all of its projects are archived.
          </p>
          <form @submit.prevent="handleDeleteWorkspace" class="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
            <label for="ws-delete-name" class="sr-only">Confirm workspace name</label>
            <input
              id="ws-delete-name"
              v-model="wsDeleteForm.confirmName"
              type="text"
              required
              :placeholder="`Type '${session.state.activeWorkspace.name}'`"
              class="input-glass px-3 py-2 text-xs"
            />
            <label for="ws-delete-password" class="sr-only">Your password</label>
            <input
              id="ws-delete-password"
              v-model="wsDeleteForm.password"
              type="password"
              required
              placeholder="Your password"
              class="input-glass px-3 py-2 text-xs"
            />
            <button
              type="submit"
              :disabled="deletingWs"
              class="btn-glass border-red-400/35 text-red-200 hover:bg-red-600 hover:text-white px-3 py-2 text-xs disabled:opacity-50"
            >
              {{ deletingWs ? 'Deleting...' : 'Delete workspace' }}
            </button>
          </form>
        </div>
      </div>

      <!-- TAB 2: CLI API KEYS -->
      <div v-if="activeTab === 'keys'" role="tabpanel" class="space-y-5">
        <div
          v-if="!canManageKeys"
          class="border border-white/[0.11] bg-[#08080B] p-6 text-xs sm:text-sm text-[#D4D4D8]"
        >
          View-only members cannot create or revoke CLI API keys.
        </div>

        <template v-else-if="session.state.activeWorkspaceId">
          <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-5">
            <div>
              <h2 class="text-sm sm:text-base font-display font-semibold text-[#F5F5F3]">
                CLI API Keys
              </h2>
              <p class="text-xs text-[#8A8D96] mt-0.5">
                Up to 5 active keys per user. Tokens are shown once when created.
              </p>
            </div>

            <form @submit.prevent="handleCreateKey" class="flex flex-wrap gap-2.5 text-xs">
              <label for="new-key-label" class="sr-only">API key label</label>
              <input
                id="new-key-label"
                v-model.trim="newKeyLabel"
                type="text"
                required
                placeholder="e.g. Work Laptop"
                class="input-glass flex-1 min-w-[220px] px-3 py-2 text-xs"
              />
              <button
                type="submit"
                :disabled="creatingKey"
                class="btn-platinum px-4 py-2 text-xs disabled:opacity-50"
              >
                <Loader2 v-if="creatingKey" class="h-3.5 w-3.5 animate-spin" />
                <span>Create API key</span>
              </button>
            </form>

            <!-- One-time Raw API Key Display -->
            <div
              v-if="createdRawKey"
              class="p-4 bg-emerald-500/10 border border-emerald-400/25 space-y-3 text-xs font-mono"
            >
              <div class="font-sans font-semibold text-emerald-300">
                Save this API key now — it won’t be shown again:
              </div>
              <div class="p-2.5 bg-[#050507] border border-white/[0.1] text-[#F5F5F3] break-all flex items-center justify-between gap-3">
                <span>{{ createdRawKey.api_key }}</span>
                <button
                  type="button"
                  @click="copyText(createdRawKey.api_key, 'API key')"
                  class="btn-glass shrink-0 px-2.5 py-1 text-xs font-sans"
                >
                  Copy key
                </button>
              </div>
              <div class="text-xs text-[#D4D4D8] break-all">
                <span class="font-sans text-[#8A8D96]">CLI command: </span>
                <span class="text-[#F5F5F3]">{{ cliConfigureCommand }}</span>
              </div>
              <button
                type="button"
                @click="copyText(cliConfigureCommand, 'CLI setup command')"
                class="text-xs font-sans font-medium text-emerald-300 hover:underline"
              >
                Copy CLI command
              </button>
            </div>

            <div class="overflow-x-auto pt-1">
              <table class="w-full text-left text-xs">
                <thead class="border-b border-white/[0.1] font-mono uppercase text-[10px] tracking-wider text-[#8A8D96]">
                  <tr>
                    <th class="py-2 pr-4">Label</th>
                    <th class="py-2 px-4">Status</th>
                    <th class="py-2 px-4">Last used</th>
                    <th class="py-2 pl-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-white/[0.08]">
                  <tr v-if="apiKeys.length === 0">
                    <td colspan="4" class="py-6 text-center text-[#8A8D96]">No API keys created yet.</td>
                  </tr>
                  <tr v-for="k in apiKeys" :key="k.id">
                    <td class="py-2.5 pr-4 font-medium text-[#F5F5F3]">{{ k.label }}</td>
                    <td class="py-2.5 px-4">
                      <span :class="k.is_active ? 'text-emerald-400 font-medium' : 'text-[#8A8D96] line-through'">
                        {{ k.is_active ? 'Active' : 'Revoked' }}
                      </span>
                    </td>
                    <td class="py-2.5 px-4 font-mono text-[#8A8D96]">
                      {{ k.last_used_at ? new Date(k.last_used_at).toLocaleString('en-US') : 'Never' }}
                    </td>
                    <td class="py-2.5 pl-4 text-right">
                      <button
                        v-if="k.is_active"
                        type="button"
                        @click="revokeKeyTarget = k"
                        class="text-red-400 hover:text-red-300 font-medium"
                      >
                        Revoke
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </div>

      <!-- TAB 3: WORKSPACE AUDIT LOGS -->
      <div v-if="activeTab === 'audit'" role="tabpanel" class="space-y-4">
        <div
          v-if="!isManager"
          class="border border-white/[0.11] bg-[#08080B] p-6 text-xs sm:text-sm text-[#D4D4D8]"
        >
          Only Workspace Managers can view the activity log.
        </div>

        <div v-else class="border border-white/[0.11] bg-[#08080B] p-6 space-y-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <h2 class="text-sm sm:text-base font-display font-semibold text-[#F5F5F3] tabular-nums">
              Activity Log ({{ auditTotal }})
            </h2>
            <div class="flex gap-2 text-xs">
              <label for="ws-audit-filter" class="sr-only">Filter action</label>
              <input
                id="ws-audit-filter"
                v-model.trim="auditActionFilter"
                type="text"
                placeholder="Filter action (e.g. USER_LOGIN)..."
                class="input-glass px-3 py-1.5 font-mono text-xs"
              />
              <button
                type="button"
                @click="loadAuditLogs(0)"
                class="btn-glass px-3.5 py-1.5 text-xs"
              >
                Apply
              </button>
            </div>
          </div>

          <SkeletonBlock v-if="loadingAudits" variant="table-row" :count="4" />

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
                    No activity entries match your filter.
                  </td>
                </tr>
                <tr v-for="log in auditLogs" :key="log.id">
                  <td class="py-2.5 pr-3 text-[#8A8D96] whitespace-nowrap font-sans">
                    {{ new Date(log.created_at).toLocaleString('en-US') }}
                  </td>
                  <td class="py-2.5 px-3 text-[#F5F5F3] font-semibold">{{ log.action }}</td>
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

          <!-- Pagination -->
          <div class="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-white/[0.08] text-xs text-[#8A8D96] tabular-nums">
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
      </div>

      <!-- TAB 4: ACCOUNT SECURITY -->
      <div v-if="activeTab === 'security'" role="tabpanel" class="space-y-6">
        <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 class="text-sm sm:text-base font-display font-semibold text-[#F5F5F3]">
                Two-Factor Authentication (TOTP)
              </h2>
              <p class="text-xs text-[#8A8D96] mt-0.5">
                Current status:
                <strong :class="session.state.user?.mfa_enabled ? 'text-emerald-400' : 'text-[#D4D4D8]'">
                  {{ session.state.user?.mfa_enabled ? 'Enabled' : 'Disabled' }}
                </strong>
              </p>
            </div>
            <button
              type="button"
              :disabled="settingUpMfa"
              @click="promptSetupMfa"
              class="btn-platinum px-4 py-2 text-xs disabled:opacity-50"
            >
              {{ settingUpMfa ? 'Generating secret...' : 'Set up authenticator' }}
            </button>
          </div>

          <div
            v-if="mfaSetup"
            class="p-4 bg-[#050507] border border-white/[0.1] space-y-3 text-xs font-mono"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <span class="font-sans text-[#8A8D96]">Secret key: </span>
                <span class="text-emerald-300 font-semibold">{{ mfaSetup.secret }}</span>
              </div>
              <button
                type="button"
                @click="copyText(mfaSetup.secret, 'Authenticator secret')"
                class="text-[#F5F5F3] hover:underline underline-offset-4 font-sans font-medium"
              >
                Copy secret
              </button>
            </div>

            <div class="flex flex-wrap items-center justify-between gap-2">
              <div class="break-all text-[#8A8D96] flex-1">
                <span class="font-sans">Setup URI: </span>{{ mfaSetup.otpauth_uri }}
              </div>
              <button
                type="button"
                @click="copyText(mfaSetup.otpauth_uri, 'Setup URI')"
                class="shrink-0 text-[#F5F5F3] hover:underline underline-offset-4 font-sans font-medium"
              >
                Copy URI
              </button>
            </div>

            <form @submit.prevent="handleVerifyMfa" class="flex flex-wrap gap-2 pt-1">
              <label for="mfa-verify-code" class="sr-only">6-digit code</label>
              <input
                id="mfa-verify-code"
                v-model.trim="mfaTestCode"
                type="text"
                inputmode="numeric"
                pattern="\d{6}"
                maxlength="6"
                required
                placeholder="6-digit code"
                class="input-glass w-36 px-3 py-1.5 text-xs tabular-nums"
              />
              <button
                type="submit"
                :disabled="verifyingMfa"
                class="btn-glass px-4 py-1.5 text-xs font-sans border-emerald-400/35 text-emerald-300 hover:bg-emerald-500/20 disabled:opacity-50"
              >
                {{ verifyingMfa ? 'Verifying...' : 'Verify code' }}
              </button>
            </form>
          </div>
        </div>

        <!-- Delete Account -->
        <div v-if="!isSuperadmin" class="border border-red-400/30 bg-red-500/[0.06] p-6 space-y-3">
          <h2 class="text-sm font-display font-semibold text-red-300">Delete Personal Account</h2>
          <p class="text-xs text-[#D4D4D8]">
            Your account cannot be deleted while you are the sole Manager of an active workspace.
          </p>
          <form @submit.prevent="handleDeleteAccount" class="flex flex-wrap gap-2.5 text-xs">
            <label for="delete-account-pw" class="sr-only">Confirm current password</label>
            <input
              id="delete-account-pw"
              v-model="deleteAccountPassword"
              type="password"
              required
              placeholder="Confirm current password"
              class="input-glass flex-1 min-w-[220px] px-3 py-2 text-xs"
            />
            <button
              type="submit"
              :disabled="deletingAccount"
              class="btn-glass border-red-400/35 text-red-200 hover:bg-red-600 hover:text-white px-4 py-2 text-xs disabled:opacity-50"
            >
              {{ deletingAccount ? 'Deleting...' : 'Delete my account' }}
            </button>
          </form>
        </div>
      </div>
    </div>

    <!-- Confirmation Dialogs -->
    <ConfirmDialog
      :open="Boolean(removeMemberTarget)"
      title="Remove workspace member?"
      :message="`Remove '${removeMemberTarget?.full_name || ''}' (${removeMemberTarget?.email || ''}) from this workspace? Their access to projects will end immediately.`"
      confirm-text="Remove member"
      variant="danger"
      :loading="removingMember"
      @confirm="confirmRemoveMember"
      @cancel="removeMemberTarget = null"
    />

    <ConfirmDialog
      :open="Boolean(revokeKeyTarget)"
      title="Revoke CLI API key?"
      :message="`Revoking '${revokeKeyTarget?.label || ''}' will immediately disable CLI uploads using this token.`"
      confirm-text="Revoke key"
      variant="danger"
      :loading="revokingKey"
      @confirm="confirmRevokeKey"
      @cancel="revokeKeyTarget = null"
    />

    <ConfirmDialog
      :open="confirmResetMfa"
      title="Generate new authenticator secret?"
      message="Two-factor authentication is already enabled on your account. Generating a new secret will replace your existing authenticator setup."
      confirm-text="Replace secret"
      variant="warning"
      :loading="settingUpMfa"
      @confirm="executeSetupMfa"
      @cancel="confirmResetMfa = false"
    />

    <!-- Audit Detail Modal -->
    <BaseModal
      :open="Boolean(selectedAuditLog)"
      title="Activity Log Details"
      max-width="lg"
      @close="selectedAuditLog = null"
    >
      <div v-if="selectedAuditLog" class="space-y-3 text-xs font-mono">
        <dl class="grid grid-cols-2 border border-white/[0.1] divide-x divide-white/[0.1] bg-[#050507]">
          <div class="p-3">
            <dt class="font-sans text-[#8A8D96] text-xs">Action</dt>
            <dd class="text-[#F5F5F3] font-semibold mt-0.5">{{ selectedAuditLog.action }}</dd>
          </div>
          <div class="p-3">
            <dt class="font-sans text-[#8A8D96] text-xs">IP Address</dt>
            <dd class="text-[#F5F5F3] mt-0.5">{{ selectedAuditLog.ip_address }}</dd>
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
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loader2 } from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import {
  api,
  type APIKeyCreateResponse,
  type APIKeySummary,
  type AuditLogEntry,
  type MFASetupResponse,
  type WorkspaceMember,
  type WorkspaceRole,
} from '@/services/api'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'

const route = useRoute()
const router = useRouter()

const tabs = [
  { id: 'team', label: 'Team & Workspaces' },
  { id: 'keys', label: 'CLI API Keys' },
  { id: 'audit', label: 'Activity Log' },
  { id: 'security', label: 'Account Security' },
] as const
const isSuperadmin = computed(() => Boolean(session.state.user?.is_superadmin))
const visibleTabs = computed(() =>
  isSuperadmin.value ? tabs.filter((t) => t.id === 'security') : tabs
)
const activeTab = ref<(typeof tabs)[number]['id']>(isSuperadmin.value ? 'security' : 'team')

watch(
  isSuperadmin,
  (admin) => {
    if (admin) {
      activeTab.value = 'security'
    }
  },
  { immediate: true }
)

const isManager = computed(() => session.activeRole.value === 'MANAGER')
const canManageKeys = computed(() => session.activeRole.value !== 'VIEWER')

const formatRole = (role: string): string => {
  if (!role) return 'Member'
  return role.charAt(0).toUpperCase() + role.slice(1).toLowerCase()
}

// Team & Workspace
const renameWorkspaceInput = ref('')
const renamingWs = ref(false)
const acceptTokenInput = ref('')
const acceptingInvite = ref(false)
const loadingTeam = ref(false)
const members = ref<WorkspaceMember[]>([])
const inviteEmail = ref('')
const inviteRole = ref<WorkspaceRole>('PENTESTER')
const inviting = ref(false)
const lastInviteToken = ref('')
const lastInviteEmail = ref('')
const removeMemberTarget = ref<WorkspaceMember | null>(null)
const removingMember = ref(false)
const wsDeleteForm = ref({ confirmName: '', password: '' })
const deletingWs = ref(false)

const lastInviteUrl = computed(() => {
  if (!lastInviteToken.value) return ''
  return `${window.location.origin}/app/register?invite=${encodeURIComponent(lastInviteToken.value)}&email=${encodeURIComponent(lastInviteEmail.value)}`
})

// API Keys
const apiKeys = ref<APIKeySummary[]>([])
const newKeyLabel = ref('')
const creatingKey = ref(false)
const createdRawKey = ref<APIKeyCreateResponse | null>(null)
const revokeKeyTarget = ref<APIKeySummary | null>(null)
const revokingKey = ref(false)
const cliConfigureCommand = computed(() => {
  if (!createdRawKey.value || !session.state.activeWorkspaceId) return ''
  const apiOrigin = import.meta.env.VITE_API_PUBLIC_URL || window.location.origin
  return `vulnflow configure --token ${createdRawKey.value.api_key} --workspace ${session.state.activeWorkspaceId} --api-url ${apiOrigin}`
})

// Audit
const auditLogs = ref<AuditLogEntry[]>([])
const auditTotal = ref(0)
const auditOffset = ref(0)
const auditLimit = 30
const auditActionFilter = ref('')
const loadingAudits = ref(false)
const selectedAuditLog = ref<AuditLogEntry | null>(null)

// Security
const mfaSetup = ref<MFASetupResponse | null>(null)
const confirmResetMfa = ref(false)
const settingUpMfa = ref(false)
const mfaTestCode = ref('')
const verifyingMfa = ref(false)
const deleteAccountPassword = ref('')
const deletingAccount = ref(false)

watch(
  () => session.state.activeWorkspace,
  (ws) => {
    renameWorkspaceInput.value = ws?.name ?? ''
  },
  { immediate: true }
)

async function loadTeamAndKeys(): Promise<void> {
  if (isSuperadmin.value) return
  const wId = session.state.activeWorkspaceId
  if (!wId) return
  loadingTeam.value = true
  try {
    members.value = await api.workspaces.listMembers(wId)
  } catch {
    members.value = []
  } finally {
    loadingTeam.value = false
  }
  if (canManageKeys.value) {
    try {
      apiKeys.value = await api.workspaces.listApiKeys(wId)
    } catch {
      apiKeys.value = []
    }
  } else {
    apiKeys.value = []
  }
  if (isManager.value) {
    await loadAuditLogs(0)
  } else {
    auditLogs.value = []
    auditTotal.value = 0
  }
}

async function loadAuditLogs(offset = 0): Promise<void> {
  if (isSuperadmin.value) return
  const wId = session.state.activeWorkspaceId
  if (!wId || !isManager.value) return
  auditOffset.value = offset
  loadingAudits.value = true
  try {
    const res = await api.workspaces.listAuditLogs(wId, {
      action: auditActionFilter.value || undefined,
      limit: auditLimit,
      offset,
    })
    auditLogs.value = res.items
    auditTotal.value = res.total
  } catch {
    auditLogs.value = []
  } finally {
    loadingAudits.value = false
  }
}

watch(
  () => route.query.invite,
  (val) => {
    if (typeof val === 'string' && val.trim() && !isSuperadmin.value) {
      activeTab.value = 'team'
      acceptTokenInput.value = val.trim()
    }
  },
  { immediate: true }
)

watch(
  () => session.state.activeWorkspaceId,
  () => {
    if (isSuperadmin.value) return
    createdRawKey.value = null
    lastInviteToken.value = ''
    void loadTeamAndKeys()
  },
  { immediate: true }
)

const handleRenameWorkspace = async () => {
  const wId = session.state.activeWorkspaceId
  if (!wId || !renameWorkspaceInput.value) return
  renamingWs.value = true
  try {
    await api.workspaces.update(wId, { name: renameWorkspaceInput.value })
    await session.refreshWorkspace()
    toast.success('Workspace name updated.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to rename workspace.')
  } finally {
    renamingWs.value = false
  }
}

const handleAcceptInvitation = async () => {
  acceptingInvite.value = true
  try {
    const joined = await api.workspaces.acceptInvitation(acceptTokenInput.value)
    acceptTokenInput.value = ''
    await session.hydrate(true)
    await session.switchWorkspace(joined.id)
    toast.success(`Joined workspace '${joined.name}' as ${formatRole(joined.role)}.`)
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Invalid invitation token.')
  } finally {
    acceptingInvite.value = false
  }
}

const handleInvite = async () => {
  const wId = session.state.activeWorkspaceId
  if (!wId) return
  inviting.value = true
  try {
    const res = await api.workspaces.inviteMember(wId, inviteEmail.value, inviteRole.value)
    lastInviteToken.value = res.invitation_token
    lastInviteEmail.value = inviteEmail.value
    inviteEmail.value = ''
    toast.success('Invitation created and sent.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to send invitation.')
  } finally {
    inviting.value = false
  }
}

const handleRoleChange = async (member: WorkspaceMember, event: Event) => {
  const wId = session.state.activeWorkspaceId
  if (!wId) return
  const selectEl = event.target as HTMLSelectElement
  const nextRole = selectEl.value as WorkspaceRole
  try {
    await api.workspaces.updateMemberRole(wId, member.user_id, nextRole)
    member.role = nextRole
    if (member.user_id === session.state.user?.id) {
      await session.hydrate(true)
    }
    toast.success(`Updated role for ${member.full_name} to ${formatRole(nextRole)}.`)
  } catch (err: unknown) {
    selectEl.value = member.role
    toast.error(err instanceof Error ? err.message : 'Unable to update member role.')
  }
}

const confirmRemoveMember = async () => {
  const member = removeMemberTarget.value
  const wId = session.state.activeWorkspaceId
  if (!member || !wId) return
  removingMember.value = true
  try {
    await api.workspaces.removeMember(wId, member.user_id)
    members.value = members.value.filter((m) => m.user_id !== member.user_id)
    removeMemberTarget.value = null
    if (member.user_id === session.state.user?.id) {
      await session.hydrate(true)
    }
    toast.success(`${member.full_name} removed from workspace.`)
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to remove member.')
  } finally {
    removingMember.value = false
  }
}

const handleDeleteWorkspace = async () => {
  const wId = session.state.activeWorkspaceId
  if (!wId) return
  deletingWs.value = true
  try {
    await api.workspaces.delete(wId, wsDeleteForm.value.password, wsDeleteForm.value.confirmName)
    wsDeleteForm.value = { confirmName: '', password: '' }
    await session.hydrate(true)
    toast.success('Workspace deleted.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to delete workspace.')
  } finally {
    deletingWs.value = false
  }
}

const handleCreateKey = async () => {
  const wId = session.state.activeWorkspaceId
  if (!wId) return
  creatingKey.value = true
  try {
    createdRawKey.value = await api.workspaces.createApiKey(wId, newKeyLabel.value)
    newKeyLabel.value = ''
    apiKeys.value = await api.workspaces.listApiKeys(wId)
    toast.success('API key created.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to create API key.')
  } finally {
    creatingKey.value = false
  }
}

const confirmRevokeKey = async () => {
  const keyItem = revokeKeyTarget.value
  const wId = session.state.activeWorkspaceId
  if (!keyItem || !wId) return
  revokingKey.value = true
  try {
    await api.workspaces.revokeApiKey(wId, keyItem.id)
    revokeKeyTarget.value = null
    apiKeys.value = await api.workspaces.listApiKeys(wId)
    toast.success('API key revoked.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to revoke API key.')
  } finally {
    revokingKey.value = false
  }
}

const promptSetupMfa = () => {
  if (session.state.user?.mfa_enabled) {
    confirmResetMfa.value = true
  } else {
    void executeSetupMfa()
  }
}

const executeSetupMfa = async () => {
  confirmResetMfa.value = false
  settingUpMfa.value = true
  try {
    mfaSetup.value = await api.auth.setupMfa()
    await session.hydrate(true)
    toast.success('Authenticator secret generated. Add it to your authenticator app.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to set up two-factor authentication.')
  } finally {
    settingUpMfa.value = false
  }
}

const handleVerifyMfa = async () => {
  verifyingMfa.value = true
  try {
    await api.auth.verifyMfa(mfaTestCode.value)
    mfaTestCode.value = ''
    toast.success('Verification code confirmed.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Invalid verification code.')
  } finally {
    verifyingMfa.value = false
  }
}

const handleDeleteAccount = async () => {
  deletingAccount.value = true
  try {
    await api.auth.deleteMe(deleteAccountPassword.value)
    await session.logout()
    toast.success('Your account has been deleted.')
    await router.push('/')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to delete account.')
  } finally {
    deletingAccount.value = false
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
