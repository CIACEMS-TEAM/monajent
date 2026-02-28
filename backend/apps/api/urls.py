from django.urls import path

from .views.auth import (
    RegisterClientView,
    RegisterAgentView,
    LoginView,
    RefreshView,
    LogoutView,
    MeView,
    OTPRequestView,
    OTPVerifyView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    PasswordResetFinalizeView,
    PasswordChangeView,
)
from .views.listings import (
    PublicListingListView,
    PublicListingDetailView,
    AgentListingListCreateView,
    AgentListingDetailView,
    AgentListingBulkActionView,
    AgentListingRenewView,
    AgentListingImageUploadView,
    AgentListingImageReorderView,
    AgentListingImageDeleteView,
    AgentListingVideoUploadView,
    AgentListingVideoDeleteView,
    AgentVideoStreamView,
    VideoHashPreCheckView,
)
from .views.packs import (
    ClientPackListCreateView,
    ClientPackDetailView,
    WatchVideoView,
    VideoStreamView,
    ClientViewHistoryListView,
    AgentViewsReceivedListView,
)
from .views.visits import (
    AgentAvailabilityListCreateView,
    AgentAvailabilityDetailView,
    AgentDateSlotListCreateView,
    AgentDateSlotDetailView,
    ListingAvailabilityView,
    ClientVisitListCreateView,
    ClientVisitCancelView,
    AgentVisitListView,
    AgentVisitConfirmView,
    AgentVisitValidateCodeView,
    AgentVisitNoShowView,
    ListingReportCreateView,
    ClientReportListView,
)
from .views.wallet import (
    AgentWalletView,
    AgentWalletEntryListView,
    AgentWalletSetPinView,
    AgentWalletChangePinView,
    AgentWithdrawalCreateView,
    AgentWithdrawalListView,
)
from .views.client import (
    ClientDashboardView,
    ClientProfileView,
    ClientFavoriteListView,
    ClientFavoriteToggleView,
    ClientSavedSearchListCreateView,
    ClientSavedSearchDetailView,
)
from .views.agent import (
    AgentProfileView,
    AgentDocumentListCreateView,
    AgentDocumentDeleteView,
    AgentKycSubmitView,
    AdminKycReviewView,
)
from .views.dashboard import (
    AgentDashboardView,
    AgentAnalyticsView,
)
from .views.payments import (
    InitiatePackPurchaseView,
    PaymentWebhookView,
    SimulatePaymentConfirmView,
    ClientPaymentHistoryView,
)
from .views.notifications import (
    NotificationListView,
    NotificationReadView,
    NotificationReadAllView,
    NotificationUnreadCountView,
)

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────
    path('auth/register/client', RegisterClientView.as_view()),
    path('auth/register/agent', RegisterAgentView.as_view()),
    path('auth/login', LoginView.as_view()),
    path('auth/refresh', RefreshView.as_view()),
    path('auth/logout', LogoutView.as_view()),
    path('auth/me', MeView.as_view()),
    path('auth/otp/request', OTPRequestView.as_view()),
    path('auth/otp/verify', OTPVerifyView.as_view()),
    path('auth/password/reset/request', PasswordResetRequestView.as_view()),
    path('auth/password/reset/verify', PasswordResetVerifyView.as_view()),
    path('auth/password/reset/finalize', PasswordResetFinalizeView.as_view()),
    path('auth/password/change', PasswordChangeView.as_view()),

    # ── Listings publics (recherche / détail) ─────────────────
    path('listings/', PublicListingListView.as_view(), name='listing-list'),
    path('listings/<int:pk>/', PublicListingDetailView.as_view(), name='listing-detail'),

    # ── Agent : CRUD annonces ─────────────────────────────────
    path('agent/listings/', AgentListingListCreateView.as_view(), name='agent-listing-list'),
    path('agent/listings/<int:pk>/', AgentListingDetailView.as_view(), name='agent-listing-detail'),
    path('agent/listings/bulk/', AgentListingBulkActionView.as_view(), name='agent-listing-bulk'),
    path('agent/listings/<int:pk>/renew/', AgentListingRenewView.as_view(), name='agent-listing-renew'),

    # ── Agent : images d'une annonce ──────────────────────────
    path('agent/listings/<int:listing_id>/images/', AgentListingImageUploadView.as_view(), name='agent-listing-image-upload'),
    path('agent/listings/<int:listing_id>/images/reorder/', AgentListingImageReorderView.as_view(), name='agent-listing-image-reorder'),
    path('agent/listings/<int:listing_id>/images/<int:pk>/', AgentListingImageDeleteView.as_view(), name='agent-listing-image-delete'),

    # ── Agent : vidéos d'une annonce ──────────────────────────
    path('agent/listings/<int:listing_id>/videos/', AgentListingVideoUploadView.as_view(), name='agent-listing-video-upload'),
    path('agent/listings/<int:listing_id>/videos/<int:pk>/', AgentListingVideoDeleteView.as_view(), name='agent-listing-video-delete'),

    # ── Agent : stream vidéo (propre contenu, sans restriction) ─
    path('agent/videos/<int:pk>/stream/', AgentVideoStreamView.as_view(), name='agent-video-stream'),

    # ── Agent : pré-check anti-fraude vidéo ──────────────────
    path('agent/videos/precheck/', VideoHashPreCheckView.as_view(), name='video-hash-precheck'),

    # ── Client : Packs ──────────────────────────────────────
    path('client/packs/', ClientPackListCreateView.as_view(), name='client-pack-list-create'),
    path('client/packs/<int:pk>/', ClientPackDetailView.as_view(), name='client-pack-detail'),

    # ── Visionnage (pay-per-view) ────────────────────────────
    path('videos/<uuid:access_key>/watch/', WatchVideoView.as_view(), name='video-watch'),
    path('videos/stream/<str:token>/', VideoStreamView.as_view(), name='video-stream'),

    # ── Client : Historique de visionnage ────────────────────
    path('client/views/', ClientViewHistoryListView.as_view(), name='client-view-history'),

    # ── Agent : Vues reçues (stats) ──────────────────────────
    path('agent/views/', AgentViewsReceivedListView.as_view(), name='agent-views-received'),

    # ── Agent : Dashboard & Analytics ──────────────────────────────
    path('agent/dashboard/', AgentDashboardView.as_view(), name='agent-dashboard'),
    path('agent/analytics/', AgentAnalyticsView.as_view(), name='agent-analytics'),

    # ── Agent : Profil & KYC ─────────────────────────────────────
    path('agent/profile/', AgentProfileView.as_view(), name='agent-profile'),
    path('agent/profile/documents/', AgentDocumentListCreateView.as_view(), name='agent-document-list'),
    path('agent/profile/documents/<int:pk>/', AgentDocumentDeleteView.as_view(), name='agent-document-delete'),
    path('agent/profile/kyc/submit/', AgentKycSubmitView.as_view(), name='agent-kyc-submit'),
    path('admin/kyc/<int:profile_id>/review/', AdminKycReviewView.as_view(), name='admin-kyc-review'),

    # ── Agent : Wallet ─────────────────────────────────────────
    path('agent/wallet/', AgentWalletView.as_view(), name='agent-wallet'),
    path('agent/wallet/entries/', AgentWalletEntryListView.as_view(), name='agent-wallet-entries'),
    path('agent/wallet/set-pin/', AgentWalletSetPinView.as_view(), name='agent-wallet-set-pin'),
    path('agent/wallet/change-pin/', AgentWalletChangePinView.as_view(), name='agent-wallet-change-pin'),
    path('agent/wallet/withdraw/', AgentWithdrawalCreateView.as_view(), name='agent-wallet-withdraw'),
    path('agent/wallet/withdrawals/', AgentWithdrawalListView.as_view(), name='agent-wallet-withdrawals'),

    # ── Agent : Disponibilités ─────────────────────────────────
    path('agent/availability/', AgentAvailabilityListCreateView.as_view(), name='agent-availability-list'),
    path('agent/availability/<int:pk>/', AgentAvailabilityDetailView.as_view(), name='agent-availability-detail'),

    # ── Agent : Créneaux ponctuels (agenda) ──────────────────
    path('agent/date-slots/', AgentDateSlotListCreateView.as_view(), name='agent-date-slot-list'),
    path('agent/date-slots/<int:pk>/', AgentDateSlotDetailView.as_view(), name='agent-date-slot-detail'),

    # ── Disponibilités d'un agent (vue client) ───────────────
    path('listings/<int:listing_id>/availability/', ListingAvailabilityView.as_view(), name='listing-availability'),

    # ── Client : Visites physiques ───────────────────────────
    path('client/visits/', ClientVisitListCreateView.as_view(), name='client-visit-list-create'),
    path('client/visits/<int:pk>/cancel/', ClientVisitCancelView.as_view(), name='client-visit-cancel'),

    # ── Agent : Gestion des visites ──────────────────────────
    path('agent/visits/', AgentVisitListView.as_view(), name='agent-visit-list'),
    path('agent/visits/<int:pk>/confirm/', AgentVisitConfirmView.as_view(), name='agent-visit-confirm'),
    path('agent/visits/<int:pk>/validate-code/', AgentVisitValidateCodeView.as_view(), name='agent-visit-validate-code'),
    path('agent/visits/<int:pk>/no-show/', AgentVisitNoShowView.as_view(), name='agent-visit-no-show'),

    # ── Signalement d'annonces ───────────────────────────────
    path('listings/<int:listing_id>/report/', ListingReportCreateView.as_view(), name='listing-report'),
    path('client/reports/', ClientReportListView.as_view(), name='client-report-list'),

    # ── Client : Dashboard + Profil ───────────────────────────
    path('client/dashboard/', ClientDashboardView.as_view(), name='client-dashboard'),
    path('client/profile/', ClientProfileView.as_view(), name='client-profile'),

    # ── Client : Favoris ──────────────────────────────────────
    path('client/favorites/', ClientFavoriteListView.as_view(), name='client-favorites'),
    path('client/favorites/<int:listing_id>/', ClientFavoriteToggleView.as_view(), name='client-favorite-toggle'),

    # ── Client : Recherches sauvegardées ──────────────────────
    path('client/saved-searches/', ClientSavedSearchListCreateView.as_view(), name='client-saved-search-list'),
    path('client/saved-searches/<int:pk>/', ClientSavedSearchDetailView.as_view(), name='client-saved-search-detail'),

    # ── Notifications ──────────────────────────────────────────
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/read/', NotificationReadView.as_view(), name='notification-read'),
    path('notifications/read-all/', NotificationReadAllView.as_view(), name='notification-read-all'),
    path('notifications/unread-count/', NotificationUnreadCountView.as_view(), name='notification-unread-count'),

    # ── Payments ────────────────────────────────────────────────
    path('client/packs/buy/', InitiatePackPurchaseView.as_view(), name='client-pack-buy'),
    path('client/payments/', ClientPaymentHistoryView.as_view(), name='client-payment-history'),
    path('payments/webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
    path('payments/simulate/<str:tx_ref>/confirm/', SimulatePaymentConfirmView.as_view(), name='payment-simulate-confirm'),
]
