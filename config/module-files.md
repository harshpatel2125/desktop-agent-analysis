# Module File Map

> Files within each section are sorted by commit frequency (most edited first).
> The number in brackets is the commit count — a rough proxy for how widely used / actively maintained the file is.

---

## 1. Calendar

**Screens**
- `app/(app)/(drawer)/(tabs)/calendar/index.tsx` (153)
- `app/(app)/(drawer)/(tabs)/calendar/[calendarId]/create.tsx` (109)
- `app/(app)/(drawer)/(tabs)/calendar/[calendarId]/[calendarEventId]/edit.tsx` (88)
- `app/(app)/(drawer)/(tabs)/calendar/[calendarId]/[calendarEventId]/index.tsx` (83)
- `app/(app)/(drawer)/(tabs)/calendar/settings/index.tsx` (21)

**Components**
- `components/calendar/CalendarSideMenu.tsx` (42)
- `components/calendar/CalendarControls/index.tsx` (41)
- `components/calendar/CalendarCustomEventComponent.tsx` (40)
- `components/calendar/Event/EventDescriptionField.tsx` (38)
- `components/calendar/Event/EventGuestsList.tsx` (37)
- `components/calendar/CalendarShadowModals/CalendarShadowNewRequestModal.tsx` (34)
- `components/calendar/CalendarControls/MenuSharedCalendars.tsx` (23)
- `components/calendar/Event/EventCalendarsSelection.tsx` (32)
- `components/calendar/Event/EventActions.tsx` (19)
- `components/calendar/CalendarControls/CalendarActions.tsx` (15)
- `components/calendar/Event/EventTimeline.tsx` (15)
- `components/calendar/CalendarShadowModals/CalendarSharedPeopleSettingsModal.tsx` (18)
- `components/calendar/CalendarControls/CalendarColourPicker.tsx` (14)
- `components/calendar/CalendarEventsOnlyMonthView.tsx` (12)
- `components/calendar/CalendarControls/CalendarSlotControl.tsx` (16)
- `components/calendar/CalendarCustomAllDayEvents.tsx` (16)
- `components/calendar/Event/EventDateTimeDetails.tsx` (6)
- `components/calendar/Event/EventLocationDetails.tsx` (6)
- `components/calendar/CalendarEventsOnlyDayView.tsx` (6)
- `components/calendar/CalendarEventsOnlyWeekView.tsx` (6)
- `components/calendar/CalendarInsights/WeeklySummarySection.tsx` (6)
- `components/calendar/CalendarControls/CalendarTopIcons.tsx` (5)
- `components/calendar/CalendarShadowModals/EditSharedCalendarInput.tsx` (9)
- `components/calendar/CalendarInsights/FocusTimeSuggestionsSection.tsx` (4)
- `components/calendar/CalendarInsights/MergeRedundantSection.tsx` (4)
- `components/calendar/CalendarInsights/ResolveOverlappingSection.tsx` (4)
- `components/calendar/Event/EventResponseButtons.tsx` (8)
- `components/calendar/MonthYearPickerModal.tsx` (2)
- `components/calendar/DraggableEventBlock.tsx` (3)
- `components/calendar/CalendarControls/CalendarInviteAnswerView.tsx` (3)
- `components/calendar/CalendarNotificationConfirmationPopUp.tsx` (3)
- `components/calendar/recurrence/RecurrenceInput.tsx` (3)
- `components/calendar/recurrence/CustomRecurrenceOptions.tsx` (2)
- `components/calendar/CalendarLocationView.tsx` (1)
- `components/calendar/Event/EditRecurringEventConfirmModal.tsx` (1)

**Hooks**
- `hooks/calendar/useCalendarEventSubmissionHandler.tsx` (17)
- `hooks/api/calendar.ts` (34)
- `hooks/api/calendar-sharing.ts` (7)
- `hooks/calendar/useCalendarEventRefetchByIDSubmissionHandler.ts` (5)

**Services / Queries / Types / Utils**
- `utils/calendar.ts` (86)
- `types/calendar.ts` (53)
- `services/api/calendar.ts` (20)
- `schemas/calendar.ts` (11)
- `enums/calendar.ts` (7)
- `queries/calendar.ts` (8)
- `utils/calendarEventsOnlyWeek.ts` (4)
- `queries/calendar-sharing.ts` (3)
- `services/api/calendar-sharing.ts` (3)
- `utils/calendar-sharing.ts` (3)

---

## 2. Chat / Messenger

**Screens**
- `app/(app)/(drawer)/(tabs)/chats/index.tsx` (91)
- `app/(app)/(drawer)/(tabs)/chats/[id]/index.tsx` (53)
- `app/(app)/(drawer)/(tabs)/chats/new-chat.tsx` (43)
- `app/(app)/(drawer)/(tabs)/chats/contact-email.tsx` (11)
- `app/(app)/(drawer)/(tabs)/chats/[id]/message-forwarder.tsx` (17)
- `app/(app)/(drawer)/(tabs)/chats/[id]/message-attachments.tsx` (5)
- `app/(app)/(drawer)/(tabs)/chats/[id]/shared-media.tsx` (5)
- `app/(app)/chat-export.tsx` (1)
- `app/(app)/chat-sources.tsx` (1)

**Components**
- `components/chat/ChatBubble.tsx` (127)
- `components/chat/ChatUI/ChatUI.tsx` (115)
- `components/chat/Topbar.tsx` (44)
- `components/chat/ChatActionMenu.tsx` (28)
- `components/chat/MessageComposer.tsx` (35)
- `components/chat/ChatUI/Message.tsx` (18)
- `components/chat/ReplyMessageBanner.tsx` (25)
- `components/chat/LinkPreview.tsx` (15)
- `components/chat/ChatContactList.tsx` (16)
- `components/chat/ChatQuickResponseModal.tsx` (13)
- `components/chat/RecipientPicker.tsx` (10)
- `components/chat/ChatReactionsList.tsx` (10)
- `components/chat/ChatActionsView.tsx` (6)
- `components/chat/SidekickMessage.tsx` (6)
- `components/chat/DeleteChatMessageModal.tsx` (8)
- `components/chat/ForwardMessageBanner.tsx` (8)
- `components/chat/ChatDrawerMenu.tsx` (7)
- `components/chat/ChatUserView.tsx` (7)
- `components/chat/SelectedMessagesIndicator.tsx` (4)
- `components/chat/ChatEmojiSelectionModal.tsx` (5)
- `components/chat/NoChatView.tsx` (5)
- `components/chat/ChatAttachmentSheet.tsx` (3)
- `components/chat/MentionSuggestions.tsx` (3)
- `components/chat/MessageSelectorView.tsx` (3)
- `components/chat/attachments/ChatAttachments.tsx` (4)
- `components/chat/pinned/PinnedMessagesBottomSheet.tsx` (3)
- `components/chat/sharedMedia/PreviewMedia.tsx` (3)
- `components/chat/sharedMedia/Links.tsx` (2)
- `components/chat/pinned/PinnedMessagesHeader.tsx` (1)
- `components/chat/sharedMedia/Files.tsx` (1)

**Hooks**
- `hooks/chat/useMessageSelection.ts` (40)
- `hooks/chat/useChatSocket.ts` (34)
- `hooks/api/chat.ts` (23)
- `hooks/chat/useChatActions.ts` (23)
- `hooks/chat/useChatMessageSearch.tsx` (14)
- `hooks/chat/useChatState.ts` (16)
- `hooks/chat/useSharedMedia.ts` (7)
- `hooks/chat/useChatEmojiActions.ts` (2)
- `hooks/chat/usePinnedMessageActions.ts` (2)
- `hooks/chat/usePinnedMessages.ts` (1)

**Services / Types / Utils**
- `types/chat.ts` (50)
- `services/api/chat.ts` (24)
- `enums/chat.ts` (14)
- `utils/chats.ts` (14)
- `types/chat-socket.ts` (2)
- `utils/socket.ts` (6)
- `utils/chatPinnedMessages.ts` (1)

**Contexts**
- `contexts/ChatUIContext.tsx` (15)
- `contexts/ChatSocketContext.tsx` (4)
- `contexts/SharedMediaUIContext.tsx` (4)
- `contexts/SocketContext.tsx` (4)

---

## 3. Emails

**Screens**
- `app/(app)/(drawer)/(tabs)/emails/[emailAccountId]/draft.tsx` (138)
- `app/(app)/(drawer)/(tabs)/emails/[emailAccountId]/[emailMessageId]/index.tsx` (72)
- `app/(app)/(drawer)/(tabs)/emails/index.tsx` (68)
- `app/(app)/(drawer)/(tabs)/emails/email-flow/index.tsx` (41)
- `app/(app)/(drawer)/(tabs)/emails/email-classic.tsx` (22)
- `app/(app)/(drawer)/(tabs)/emails/email-priorities.tsx` (12)
- `app/(app)/(drawer)/(tabs)/emails/email-flow/[emailAccountId]/[emailMessageId]/[action].tsx` (18)
- `app/(app)/(drawer)/(tabs)/emails/priorities-flow.tsx` (2)

**Components**
- `components/emails/EmailBodyEditor.tsx` (90)
- `components/emails/EmailsList.tsx` (48)
- `components/emails/Draft/AiDraftButton.tsx` (37)
- `components/emails/List/EmailListItem.tsx` (42)
- `components/emails/EmailFlow/EmailDetails.tsx` (25)
- `components/emails/EmailFlow/HorizontalSwiper.tsx` (21)
- `components/emails/EmailSideMenu.tsx` (22)
- `components/emails/EmailAccountDropdownMenu.tsx` (13)
- `components/emails/Details/EmailActions.tsx` (15)
- `components/emails/Draft/DraftActions.tsx` (15)
- `components/emails/EmailFlow/VerticalSwiper.tsx` (15)
- `components/emails/List/EmailSelection.tsx` (14)
- `components/emails/List/EmailCategoriesDropdown.tsx` (10)
- `components/emails/Draft/CustomDraftRecipientsInput.tsx` (31)
- `components/emails/EmailFlow/ActionButtons.tsx` (12)
- `components/emails/Details/RecipientsDetailsBox.tsx` (8)
- `components/emails/TopEmailsTabBar.tsx` (8)
- `components/emails/EmailFlow/InboxSelectionModal.tsx` (6)
- `components/emails/EmailPriorities/PriorityCategoryCard/index.tsx` (6)
- `components/emails/EmailScheduleModal.tsx` (6)
- `components/emails/EmailAccountSelection.tsx` (4)
- `components/emails/EmailPriorities/PrioritySummaryCard.tsx` (4)
- `components/emails/Details/EmailMessageHeader.tsx` (2)
- `components/emails/EmailPriorities/SuggestedEvent.tsx` (2)
- `components/emails/EmailPriorities/SuggestedTask.tsx` (2)
- `components/emails/EmailPriorities/PriorityCategoryCard/SwipeableEmailRow.tsx` (3)
- `components/emails/EmailPriorities/SnoozeBottomSheet.tsx` (1)
- `components/emails/EmailFAB.tsx` (1)
- `components/emails/TagsFilterSheet.tsx` (0)
- `components/emails/EmailFilterSheet.tsx` (0)

**Hooks**
- `hooks/api/emails.ts` (55)
- `hooks/emails/useEmailFlowManager.tsx` (42)
- `hooks/emails/useEmailActionFlow.tsx` (30)
- `hooks/emails/useDebouceUpdateDraft.tsx` (7)
- `hooks/emails/useEmailAccounts.tsx` (5)
- `hooks/emails/useEmailSnooze.ts` (3)
- `hooks/emails/useDraftBackgroundDetector.tsx` (2)
- `hooks/emails/usePriorityEmailSummary.ts` (1)

**Services / Queries / Types / Utils**
- `services/api/emails.ts` (51)
- `types/emails.ts` (48)
- `queries/emails.ts` (20)
- `utils/emails.ts` (25)
- `utils/html.ts` (1)
- `utils/emailPriorities.ts` (1)
- `utils/replyTracker.ts` (1)

**Contexts**
- `contexts/EmailListContext.tsx` (6)
- `contexts/OutboxContext.tsx` (4)
- `contexts/EmailFlowAllScreensContext.tsx` (2)
- `contexts/EmailDoneStateContext.tsx` (1)

---

## 4. Notes

**Screens**
- `app/(app)/(drawer)/(tabs)/notes/new/index.tsx` (148)
- `app/(app)/(drawer)/(tabs)/notes/index.tsx` (60)
- `app/(app)/(drawer)/(tabs)/notes/[noteId]/index.tsx` (15)

**Components**
- `components/notes/Note/AiNoteButton.tsx` (59)
- `components/notes/NoteView.tsx` (36)
- `components/notes/NoteActionsModal.tsx` (11)
- `components/notes/NoteEditorContent.tsx` (9)
- `components/notes/NoteEditorToolbar.tsx` (8)
- `components/notes/NoteEditorTitleInput.tsx` (5)
- `components/notes/NoteInfoModal.tsx` (4)
- `components/notes/CustomDropdown.tsx` (4)
- `components/notes/HyperlinkModal.tsx` (2)
- `components/notes/NoteEditorPreviousContent.tsx` (2)

**Hooks**
- `hooks/api/notes.ts` (21)
- `hooks/note/useNoteInitialization.ts` (5)
- `hooks/note/useNoteNavigation.ts` (5)
- `hooks/note/useNoteActions.ts` (4)
- `hooks/note/useNoteAutoSave.ts` (4)
- `hooks/note/useNoteHistory.ts` (4)
- `hooks/note/useNoteForm.ts` (2)

**Services / Queries / Types / Utils**
- `utils/notes.ts` (26)
- `services/api/notes.ts` (16)
- `types/note.ts` (17)
- `queries/notes.ts` (8)
- `schemas/note.ts` (5)
- `utils/noteEditor.ts` (3)
- `utils/noteEditorConstants.ts` (3)
- `utils/shareNote.ts` (1)

---

## 5. Tasks

**Screens**
- `app/(app)/(drawer)/(tabs)/tasks/create-task.tsx` (127)
- `app/(app)/(drawer)/(tabs)/tasks/[id]/index.tsx` (76)
- `app/(app)/(drawer)/(tabs)/tasks/index.tsx` (63)

**Components**
- `components/tasks/Task/TaskDetailDescription.tsx` (69)
- `components/tasks/TaskItemView.tsx` (27)
- `components/tasks/Task/TaskDetailChecklist.tsx` (17)
- `components/tasks/TaskSideMenu.tsx` (11)
- `components/tasks/AddPeopleFilterView.tsx` (14)
- `components/tasks/task-required/TaskTimeRequired.tsx` (8)
- `components/tasks/Task/TaskBasicInfo.tsx` (2)
- `components/tasks/Task/TaskBreakdownModal.tsx` (3)

**Hooks**
- `hooks/api/tasks.ts` (16)

**Services / Queries / Types / Utils**
- `services/api/tasks.ts` (23)
- `types/task.ts` (37)
- `utils/tasks.ts` (21)
- `enums/task.ts` (19)
- `queries/tasks.ts` (7)
- `schemas/task.ts` (3)

---

## 6. Home (Dashboard)

**Screens**
- `app/(app)/(drawer)/(tabs)/index.tsx` (64)

**Components**
- `components/home/HomeItem.tsx` (37)

**Features**
- `features/home/views/HomeView.tsx` (11)
- `features/home/components/TodaySummaryCard.tsx` (7)
- `features/home/components/ScheduleSection.tsx` (4)
- `features/home/components/TasksSection.tsx` (3)
- `features/home/components/VideoGuideSection.tsx` (3)
- `features/home/components/WorkspaceEmailTile.tsx` (3)
- `features/home/components/WorkspaceMessageTile.tsx` (3)
- `features/home/components/WorkspaceTileCard.tsx` (3)
- `features/home/components/ScheduleEventRow.tsx` (2)
- `features/home/components/SectionHeader.tsx` (2)
- `features/home/components/TaskRow.tsx` (2)
- `features/home/components/WorkspaceSection.tsx` (2)
- `features/home/components/AiSuggestionRow.tsx` (1)
- `features/home/components/AiSuggestionsSection.tsx` (1)
- `features/home/components/SectionCtaCard.tsx` (1)
- `features/home/components/SectionDoneState.tsx` (1)

**Hooks**
- `features/home/hooks/useTodaySchedule.ts` (5)
- `features/home/hooks/useHomeTasks.ts` (4)
- `features/home/hooks/usePriorityEmailCount.ts` (4)
- `features/home/hooks/useUnreadChats.ts` (2)
- `features/home/hooks/useEmailConnection.ts` (2)
- `features/home/hooks/useCalendarConnection.ts` (1)
- `hooks/api/home.ts` (3)

**Services / Queries**
- `services/api/home.ts` (2)
- `queries/home.ts` (3)

---

## 7. Ask Warp / AI Assistant

**Screens**
- `app/(app)/ai-assistant.tsx` (46)
- `app/(app)/personalization/index.tsx` (2)
- `app/(app)/ai-assistant-screen.tsx` (1)
- `app/(app)/chat-export.tsx` (1)
- `app/(app)/chat-sources.tsx` (1)
- `app/(app)/personalization/ai-profile.tsx` (1)

**Components**
- `components/chat-ai/index.tsx` (111)
- `components/chat-ai/ChatAssistantBubble.tsx` (59)
- `components/ws-tools/WSToolsModal.tsx` (60)
- `components/chat-ai/ChatEntryView.tsx` (39)
- `components/chat-ai/AssistantBubbleControls.tsx` (28)
- `components/chat-ai/AttachmentModal.tsx` (24)
- `components/ws-tools/WSSummariseModal.tsx` (22)
- `components/ws-tools/WSCreateToolsView.tsx` (21)
- `components/ai-assistant/Composer.tsx` (16)
- `components/ws-tools/WSToolsItemContent.tsx` (11)
- `components/chat-ai/ChatSideMenu.tsx` (17)
- `components/chat-ai/ChatHeaderView.tsx` (6)
- `components/chat-ai/SourceCard.tsx` (7)
- `components/chat-ai/ChatInputControls.tsx` (9)
- `components/ws-tools/ToneChangeView.tsx` (5)
- `components/ws-tools/WSSynonymsView.tsx` (5)
- `components/animations/AIBottomSheetSuggestions.tsx` (6)
- `components/ai-assistant/BottomSheetShell.tsx` (6)
- `components/chat-ai/ImageViewerModal.tsx` (3)
- `components/animations/AnimatedPrompts.tsx` (1)
- `components/ai-assistant/AnswerLengthDropdown.tsx` (1)

**Features**
- `features/warp-assistant/views/WarpAssistant.tsx` (2)
- `features/personalization/views/PersonalizationView.tsx` (5)
- `features/personalization/views/AIProfileView.tsx` (4)
- `features/personalization/components/TrainAIEntryView.tsx` (3)
- `features/personalization/components/EditMemoryPopup.tsx` (2)
- `features/personalization/components/PersonalizationCard.tsx` (1)
- `features/chat-ai/views/ExportDocumentScreen.tsx` (1)
- `features/chat-ai/views/SourcesScreen.tsx` (1)

**Hooks**
- `hooks/ai/useAssistantManager.ts` (31)
- `hooks/api/personalization.ts` (8)
- `hooks/ai/useActiveChildParams.ts` (3)
- `hooks/api/proofread.ts` (3)
- `hooks/ai/useAiChatStream.ts` (1)
- `hooks/ai/usePersistedBottomSheetConversation.ts` (1)

**Services / Types / Utils**
- `types/chat-ai.ts` (5)
- `utils/markdown.ts` (5)
- `utils/ws-tools.ts` (3)
- `services/api/personalization.ts` (3)
- `services/api/aiChatMessage.ts` (2)
- `utils/sse.ts` (1)
- `services/api/aiChatStream.ts` (1)
- `types/aiChatStream.ts` (1)

**Contexts**
- `contexts/WsToolsContext.tsx` (2)
- `contexts/ToolsMenuContext.tsx` (4)
- `contexts/CreditModalsContext.tsx` (2)

---

## 8. Contacts

**Screens**
- `app/(app)/(drawer)/(tabs)/contacts/[contactId]/details.tsx` (20)
- `app/(app)/(drawer)/(tabs)/contacts/index.tsx` (19)
- `app/(app)/(drawer)/(tabs)/contacts/[contactId]/miniDetails.tsx` (12)
- `app/(app)/(drawer)/(tabs)/contacts/group-details.tsx` (10)
- `app/(app)/(drawer)/(tabs)/contacts/manage/[mode].tsx` (8)

**Components**
- `components/contacts/ContactList.tsx` (24)
- `components/contacts/AddEdit/ContactForm.tsx` (20)
- `components/contacts/Details/Email.tsx` (15)
- `components/contacts/Details/RecentEventsAndTasks.tsx` (12)
- `components/contacts/Details/ContactSettings.tsx` (11)
- `components/contacts/Details/Labels.tsx` (8)
- `components/contacts/Details/Phone.tsx` (8)
- `components/contacts/AddEdit/ProfilePictureSetup.tsx` (8)
- `components/contacts/AddEdit/birthday/BirthdayPicker.tsx` (8)
- `components/contacts/AddEdit/contactInfo/MultipleValuesInput.tsx` (8)
- `components/contacts/ContactFilters.tsx` (8)
- `components/contacts/ContactAccountSelection.tsx` (6)
- `components/contacts/Details/BasicInfo.tsx` (6)
- `components/contacts/Details/ContactActionsModal.tsx` (2)
- `components/contacts/GroupDetails.tsx` (7)
- `components/contacts/AlphaScrollBar.tsx` (2)

**Hooks**
- `hooks/contacts/useContactManagement.ts` (13)
- `hooks/api/contacts.ts` (12)
- `hooks/contacts/useNoteHandler.ts` (6)
- `hooks/contacts/useProfilePicRedirection.ts` (5)

**Services / Queries / Types / Utils**
- `utils/contacts.ts` (22)
- `types/contacts.ts` (11)
- `services/api/contacts.ts` (9)
- `queries/contacts.ts` (3)

**Contexts**
- `contexts/ContactsContext.tsx` (4)

---

## 9. Integrations

**Screens**
- `app/(app)/(drawer)/(tabs)/user-centre/integrations/index.tsx` (52)
- `app/(app)/(drawer)/(tabs)/user-centre/integrations/[id]/index.tsx` (34)
- `app/(app)/(drawer)/(tabs)/user-centre/integrations/[id]/[accountId]/index.tsx` (27)
- `app/(app)/(drawer)/(tabs)/user-centre/integrations/[id]/[accountId]/delete.tsx` (12)
- `app/(app)/(drawer)/(tabs)/user-centre/integrations/[id]/password-setup/index.tsx` (1)
- `app/(app)/integrations-modal.tsx` (1)

**Components**
- `components/integration/Integration.tsx` (66)
- `components/integration/IntegrationActionRequired.tsx` (20)
- `components/integration/PasswordSetup.tsx` (13)
- `components/integration/IntegrationsContent.tsx` (2)
- `components/integration/SubscriptionStatusBanner.tsx` (4)

**Hooks**
- `hooks/api/integrations.ts` (13)
- `hooks/integrations/useConnectIntegration.ts` (6)

**Services / Queries / Types**
- `types/integration.ts` (12)
- `services/api/integrations.ts` (10)
- `queries/integrations.ts` (4)
- `utils/oauth.ts` (4)

---

## 10. User Centre / Settings

**Screens**
- `app/(app)/(drawer)/(tabs)/user-centre/index.tsx` (37)
- `app/(app)/(drawer)/(tabs)/user-centre/my-profile/index.tsx` (37)
- `app/(app)/(drawer)/(tabs)/user-centre/account-details/index.tsx` (34)
- `app/(app)/(drawer)/(tabs)/user-centre/subscription-plan/index.tsx` (33)
- `app/(app)/(drawer)/(tabs)/user-centre/help-and-support/index.tsx` (28)
- `app/(app)/(drawer)/(tabs)/user-centre/integrations/[id]/[accountId]/index.tsx` (27)
- `app/(app)/(drawer)/(tabs)/user-centre/my-settings/index.tsx` (13)
- `app/(app)/(drawer)/(tabs)/user-centre/video-guides/index.tsx` (11)
- `app/(app)/(drawer)/(tabs)/user-centre/privacy-centre/index.tsx` (15)
- `app/(app)/(drawer)/(tabs)/user-centre/my-profile/change-password.tsx` (2)
- `app/(app)/(drawer)/(tabs)/user-centre/permissions/index.tsx` (2)
- `app/(app)/(drawer)/(tabs)/user-centre/subscription-plan/manage/index.tsx` (7)

**Features**
- `features/profile/hooks/useProfileEditorController.ts` (3)
- `features/profile/views/ProfileEditorView.tsx` (2)
- `features/profile/views/ChangePasswordView.tsx` (2)
- `features/profile/components/ProfileField.tsx` (2)
- `features/profile/components/ProfileActionButton.tsx` (1)
- `features/profile/components/ProfileAvatarPicker.tsx` (1)
- `features/profile/components/ProfileHeader.tsx` (1)
- `features/profile/hooks/useChangePasswordController.ts` (1)
- `features/user-centre/components/UserCentreAvatar.tsx` (2)
- `features/user-centre/components/UserCentreProfileCard.tsx` (2)
- `features/user-centre/components/UserCentreScreenView.tsx` (2)
- `features/user-centre/components/UserCentreMenuItem.tsx` (1)
- `features/user-centre/components/UserCentreMenuList.tsx` (1)

**Subscription Components**
- `components/subscription/SubscriptionCard.tsx` (26)
- `components/subscription/CreditsPanel.tsx` (16)
- `components/subscription/credits/CreditWarningModal.tsx` (11)
- `components/subscription/credits/CreditRunningLowModal.tsx` (8)
- `components/subscription/TopUpModal.tsx` (5)
- `components/subscription/SubscriptionPlanTabs.tsx` (3)
- `components/subscription/PlanTab.tsx` (2)

**Hooks**
- `hooks/iap/useInAppPayment.tsx` (19)
- `hooks/api/users.ts` (12)
- `hooks/api/subscription.ts` (9)
- `hooks/credits/credits.ts` (10)

**Services / Queries / Utils**
- `services/api/subscriptions.ts` (20)
- `queries/users.ts` (5)
- `queries/subscriptions.ts` (3)
- `services/api/users.ts` (9)
- `types/users.ts` (2)
- `utils/subscriptions.ts` (6)
- `utils/credits.ts` (5)

---

## 11. Auth / Onboarding

**Screens**
- `app/login.tsx` (78)
- `app/register/verify.tsx` (33)
- `app/welcome.tsx` (15)
- `app/register/connect-service.tsx` (8)
- `app/marketing.tsx` (8)
- `app/register/interests.tsx` (7)
- `app/register/create-account.tsx` (5)
- `app/register/permissions/notifications.tsx` (4)
- `app/reset-password.tsx` (4)
- `app/register/benefits.tsx` (2)
- `app/register/permissions/location.tsx` (2)

**Features**
- `features/onboarding/data/interests.ts` (5)
- `features/onboarding/components/SignupStepLayout.tsx` (4)
- `features/onboarding/components/OnboardingMascotCard.tsx` (2)
- `features/onboarding/data/connectServices.tsx` (1)

**Hooks**
- `hooks/api/auth.ts` (36)
- `hooks/init/useInitUser.ts` (5)
- `hooks/init/useInitStoredUserDetails.ts` (1)
- `hooks/api/onboarding.ts` (1)
- `hooks/permissions/useNotificationsPermissionTrigger.ts` (1)
- `hooks/permissions/useLocationPermissionTrigger.ts` (1)

**Services / Types**
- `schemas/auth.ts` (20)
- `services/api/auth.ts` (16)
- `types/auth.ts` (14)
- `utils/validators.ts` (10)
- `services/api/onboarding.ts` (1)

---

## 12. Shared / Common Components

> Used across multiple modules. Sorted by commit count.

### UI Elements (`components/ui/`)

| Commits | Component | Purpose |
|---------|-----------|---------|
| 22 | `ui/layout/CollapsibleHeader.tsx` | Scroll-collapsible header layout |
| 18 | `ui/elements/typography/Typography.tsx` | All text — `Body`, `H1`–`H5`, `Small`, `Caption`, etc. |
| 15 | `ui/layout/ScreenContainer.tsx` | Full-screen wrapper with safe area |
| 13 | `ui/elements/button/Button.tsx` | Primary button with variants and loading state |
| 9 | `ui/elements/menu/ActionMenu.tsx` | Contextual action menu |
| 9 | `ui/form/CheckboxWithLabel.tsx` | Checkbox with label |
| 7 | `ui/elements/common/TopControlBar.tsx` | Top bar with title + actions |
| 5 | `ui/elements/common/PressableOpacity.tsx` | Touchable with opacity — used everywhere |
| 5 | `ui/elements/common/TextLink.tsx` | Inline tappable text link |
| 4 | `ui/elements/header/HeaderBar.tsx` | Slim header bar |
| 4 | `ui/form/LabeledField.tsx` | Input with floating label |
| 3 | `ui/elements/common/GlassPill.tsx` | Pill-shaped tag/badge |
| 3 | `ui/elements/divider/DividerWithText.tsx` | Horizontal rule with centred label |
| 3 | `ui/elements/header/HeaderWithSquareBack.tsx` | Header with square back button |
| 3 | `ui/elements/header/TitleAndSubtitleHeader.tsx` | Two-line header |
| 2 | `ui/elements/button/HapticPressable.tsx` | Pressable with haptic feedback |
| 2 | `ui/elements/common/FloatingIconButton.tsx` | Icon-only floating button for headers |
| 2 | `ui/elements/common/SearchBar.tsx` | Reusable search input |
| 2 | `ui/elements/header/Header.tsx` | Screen header |
| 2 | `ui/form/Counter.tsx` | Numeric increment/decrement |
| 2 | `ui/layout/AndroidKeyboardAdjust.tsx` | Android keyboard inset helper |
| 1 | `ui/elements/button/BackButton.tsx` | Back navigation button |
| 1 | `ui/elements/divider/DividerStandard.tsx` | Horizontal rule |
| 1 | `ui/elements/input/Input.tsx` | Base text input |
| 1 | `ui/elements/loading-dots/LoadingDots.tsx` | Animated loading indicator |
| 1 | `ui/elements/loading-dots/ThinkingBubble.tsx` | AI thinking animation |

### Root-Level Shared Components (`components/`)

| Commits | Component | Purpose |
|---------|-----------|---------|
| 74 | `SvgComponent.tsx` | Slug-based SVG loader — icons and illustrations everywhere |
| 35 | `MessageBubble.tsx` | Generic message bubble |
| 18 | `UserProfileImage.tsx` | Circular user avatar with image or initials fallback |
| 17 | `ThemedText.tsx` | Theme-aware text wrapper |
| 13 | `RenderHtmlComponent.tsx` | Renders HTML content safely |
| 10 | `Checkbox.tsx` | Standalone checkbox |
| 10 | `MenuItem.tsx` | Single row menu item |
| 9 | `DeviceImagePicker.tsx` | Camera/gallery image picker |
| 9 | `EmojiSelector.tsx` | Emoji picker |
| 8 | `ColorSelectModal.tsx` | Colour picker modal |
| 7 | `ActivityContentLoader.tsx` | Skeleton/shimmer loader |
| 7 | `UserRoundedInitialsCircle.tsx` | Initials avatar — chat, contacts, calendar guests |
| 6 | `BlurredBackground.tsx` | Blurred overlay backdrop |
| 6 | `HorizontalLine.tsx` | Thin divider line |
| 6 | `PersonAvatar.tsx` | Generic person avatar |
| 6 | `ToggleSwitch.tsx` | On/off toggle |
| 6 | `ai-assistant/BottomSheetShell.tsx` | Core sheet engine — all bottom sheets use this |
| 5 | `ConfirmationAlert.tsx` | Confirm/cancel alert dialog |
| 3 | `ThemedView.tsx` | Theme-aware view wrapper |
| 2 | `EmptyListView.tsx` | Empty state placeholder for lists |
| 2 | `FloatingActionButton.tsx` | FAB (add/create button) |
| 0 | `BottomSheetModal.tsx` | RN Modal + BottomSheetShell wrapper (new — used by every feature's bottom sheets) |

### Shared Hooks & Services

| Commits | File | Purpose |
|---------|------|---------|
| 20 | `hooks/api/tags.ts` | Tagging system — emails, tasks, notes |
| 13 | `hooks/sort-filter/useSortFilterManager.ts` | Shared sort & filter state for all list screens |
| 10 | `hooks/api/notifications.ts` | Push notification queries |
| 9 | `hooks/attachments/useModuleItemsAsAttachments.ts` | Attach tasks/notes/events to messages |
| 8 | `services/api/tags.ts` | Tag API calls |
| 5 | `services/api/items.ts` | Cross-module item references |
| 3 | `hooks/useDebounceInput.ts` | Input debounce — used in search fields everywhere |

### Shared Contexts

| Commits | Context | Purpose |
|---------|---------|---------|
| 16 | `contexts/CollapsibleHeaderContext.tsx` | Header collapse state |
| 5 | `contexts/LocationContext.tsx` | Location permission + current coords |
| 4 | `contexts/NotificationsContext.tsx` | In-app notification toasts |
| 3 | `contexts/NetworkContext.tsx` | Online/offline status |
| 3 | `contexts/WalkthroughContext.tsx` | Walkthrough / guided tour state |
| 2 | `contexts/CreateMenuContext.tsx` | Global "create new" FAB menu |
| 1 | `contexts/RemoteConfigContext.tsx` | Firebase Remote Config values |
