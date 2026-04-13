<script setup lang="ts">
import logoUrl from '@/assets/icons/logo_monajent_header.webp'
</script>

<template>
  <div class="legal-page">
    <header class="legal-header">
      <div class="legal-header__inner">
        <router-link to="/home" class="legal-back" aria-label="Retour">
          <svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
        </router-link>
        <router-link to="/home">
          <img :src="logoUrl" alt="MonaJent" class="legal-logo" />
        </router-link>
      </div>
    </header>

    <main class="legal-content">
      <h1>Politique de Confidentialité</h1>
      <p class="legal-meta">Dernière mise à jour : 13 avril 2026 — Version 2026-04-13-v2</p>

      <section>
        <h2>1. Introduction</h2>
        <p>La présente politique de confidentialité décrit la manière dont Monajent collecte, utilise et protège les données personnelles des utilisateurs, conformément à la loi n°2013-450 du 19 juin 2013 relative à la protection des données à caractère personnel en Côte d'Ivoire.</p>
        <p>Monajent s'engage à protéger la vie privée de ses utilisateurs et à traiter les données personnelles de manière transparente et responsable.</p>
      </section>

      <section>
        <h2>2. Responsable du traitement</h2>
        <p>Le responsable du traitement des données est :</p>
        <ul>
          <li><strong>CIACEMS</strong></li>
          <li>Email : itciacems@gmail.com</li>
          <li>Téléphone : +225 27 22 30 08 40</li>
        </ul>
      </section>

      <section>
        <h2>3. Données collectées</h2>
        <p><strong>Pour les agents :</strong></p>
        <ul>
          <li>Nom et prénom</li>
          <li>Numéro de téléphone</li>
          <li>Adresse email (optionnelle)</li>
          <li>Zone d'activité</li>
          <li>Pièce d'identité (scan/photo)</li>
          <li>Contenus publiés (vidéos, photos, descriptions d'annonces)</li>
        </ul>
        <p><strong>Pour les utilisateurs :</strong></p>
        <ul>
          <li>Numéro de téléphone</li>
          <li>Nom d'utilisateur</li>
          <li>Informations de navigation et préférences de recherche</li>
          <li>Historique d'utilisation (annonces consultées, favoris)</li>
          <li>Données vocales traitées localement lors de l'utilisation de l'assistante IA Mona (non stockées sur nos serveurs)</li>
        </ul>
      </section>

      <section>
        <h2>4. Finalité de la collecte</h2>
        <p>Les données sont collectées pour :</p>
        <ul>
          <li>créer et gérer les comptes utilisateurs</li>
          <li>vérifier l'identité des agents</li>
          <li>sécuriser la plateforme et prévenir la fraude</li>
          <li>améliorer les services et l'expérience utilisateur</li>
          <li>faciliter la mise en relation entre agents et utilisateurs</li>
          <li>personnaliser les résultats de recherche via l'intelligence artificielle</li>
        </ul>
        <p>En cas d'introduction future de services payants, les données pourront également être utilisées pour la gestion des transactions. Les utilisateurs en seront informés préalablement.</p>
      </section>

      <section>
        <h2>5. Données sensibles (pièces d'identité)</h2>
        <p>Les pièces d'identité sont collectées <strong>uniquement</strong> pour vérifier l'authenticité des agents et renforcer la confiance sur la plateforme. Elles ne sont jamais partagées avec des tiers sans consentement.</p>
      </section>

      <section>
        <h2>6. Intelligence artificielle et données vocales</h2>
        <p>L'assistante IA Mona utilise la reconnaissance vocale du navigateur pour faciliter la recherche. Les données vocales sont :</p>
        <ul>
          <li>traitées localement par le navigateur de l'utilisateur</li>
          <li>converties en texte qui est ensuite envoyé à nos serveurs pour l'analyse de recherche</li>
          <li><strong>non enregistrées ni stockées</strong> sous forme audio sur nos serveurs</li>
        </ul>
        <p>Les requêtes textuelles issues de la reconnaissance vocale peuvent être utilisées de manière anonymisée pour améliorer la qualité du service de recherche.</p>
      </section>

      <section>
        <h2>7. Durée de conservation</h2>
        <p>Les données sont conservées :</p>
        <ul>
          <li>pendant la durée d'utilisation du compte</li>
          <li>ou jusqu'à demande de suppression par l'utilisateur</li>
        </ul>
        <p>Après suppression du compte, les données personnelles sont effacées dans un délai raisonnable, sauf obligation légale de conservation.</p>
      </section>

      <section>
        <h2>8. Sécurité des données</h2>
        <p>Monajent met en œuvre :</p>
        <ul>
          <li>des mesures techniques de sécurité (chiffrement HTTPS, authentification JWT, accès restreints)</li>
          <li>des systèmes de protection contre les accès non autorisés</li>
          <li>des sauvegardes régulières des données</li>
          <li>une journalisation des accès aux données sensibles</li>
        </ul>
      </section>

      <section>
        <h2>9. Droits des utilisateurs</h2>
        <p>Conformément à la loi n°2013-450, vous disposez des droits suivants :</p>
        <ul>
          <li><strong>Droit d'accès</strong> : obtenir confirmation du traitement de vos données</li>
          <li><strong>Droit de rectification</strong> : corriger des données inexactes</li>
          <li><strong>Droit de suppression</strong> : demander l'effacement de vos données</li>
          <li><strong>Droit d'opposition</strong> : vous opposer au traitement de vos données</li>
        </ul>
        <p>Pour exercer ces droits, contactez-nous à : <strong>itciacems@gmail.com</strong></p>
      </section>

      <section>
        <h2>10. Partage des données</h2>
        <p>Les données ne sont pas vendues. Elles peuvent être partagées uniquement avec :</p>
        <ul>
          <li>des prestataires techniques (hébergement, services d'intelligence artificielle)</li>
          <li>les autorités si la loi l'exige</li>
        </ul>
        <p>En cas d'introduction future de services de paiement, les données nécessaires pourront être partagées avec les prestataires de paiement concernés, dans le strict cadre de la transaction.</p>
      </section>

      <section>
        <h2>11. Cookies et stockage local</h2>
        <p>La plateforme utilise :</p>
        <ul>
          <li>des cookies techniques pour assurer le bon fonctionnement du service (authentification, session)</li>
          <li>le stockage local du navigateur (localStorage) pour mémoriser les préférences utilisateur</li>
        </ul>
        <p>Aucun cookie de traçage publicitaire n'est utilisé.</p>
      </section>

      <section>
        <h2>12. Modification de la politique</h2>
        <p>Cette politique peut être modifiée à tout moment, notamment en cas d'évolution du service ou de son modèle économique. Les utilisateurs seront informés de tout changement significatif.</p>
      </section>
    </main>
  </div>
</template>

<style scoped>
.legal-page { min-height: 100vh; background: #fff; }
.legal-header { padding: 16px 0; border-bottom: 1px solid #E0E0E0; }
.legal-header__inner { width: min(800px, 92vw); margin: 0 auto; padding: 0 24px; display: flex; align-items: center; gap: 12px; }
.legal-logo { height: 32px; width: auto; }
.legal-back { display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; color: #272727; transition: background .15s; text-decoration: none; }
.legal-back:hover { background: #f2f2f2; }
.legal-content { max-width: 800px; margin: 0 auto; padding: 40px 24px 80px; }
.legal-content h1 { font-size: 28px; font-weight: 700; color: #0F0F0F; margin-bottom: 8px; }
.legal-meta { font-size: 13px; color: #606060; margin-bottom: 32px; }
.legal-content h2 { font-size: 18px; font-weight: 600; color: #0F0F0F; margin: 28px 0 10px; }
.legal-content p { font-size: 15px; color: #272727; line-height: 1.7; margin-bottom: 12px; }
.legal-content ul { padding-left: 24px; margin-bottom: 12px; }
.legal-content li { font-size: 15px; color: #272727; line-height: 1.7; margin-bottom: 4px; }
.legal-content section { border-bottom: 1px solid #f2f2f2; padding-bottom: 8px; }
.legal-content section:last-child { border-bottom: none; }
@media (max-width: 600px) {
  .legal-content h1 { font-size: 22px; }
  .legal-content { padding: 24px 16px 60px; }
}
</style>
