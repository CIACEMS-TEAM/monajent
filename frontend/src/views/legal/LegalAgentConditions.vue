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
      <h1>Conditions Spécifiques Agents</h1>
      <p class="legal-meta">Dernière mise à jour : 13 avril 2026 — Version 2026-04-13-v2</p>

      <section>
        <h2>1. Objet</h2>
        <p>Les présentes conditions définissent les règles spécifiques applicables aux agents immobiliers utilisant la plateforme Monajent pour publier et promouvoir des biens immobiliers.</p>
        <p>Monajent vise à offrir aux agents un <strong>outil moderne et futuriste</strong> pour optimiser leur travail, gagner en visibilité et offrir une expérience unique à leurs clients.</p>
        <p>Ces conditions s'appliquent en complément des <router-link to="/legal/cgu">Conditions Générales d'Utilisation</router-link> et de la <router-link to="/legal/confidentialite">Politique de Confidentialité</router-link>.</p>
      </section>

      <section>
        <h2>2. Vérification des agents</h2>
        <p>L'agent accepte de fournir :</p>
        <ul>
          <li>une pièce d'identité valide</li>
          <li>des informations exactes et à jour</li>
        </ul>
        <p>Monajent se réserve le droit de valider ou refuser un profil, et de suspendre un agent en cas de doute ou de fraude.</p>
      </section>

      <section>
        <h2>3. Publication des biens</h2>
        <p>L'agent s'engage à :</p>
        <ul>
          <li>publier uniquement des biens <strong>réels et disponibles</strong></li>
          <li>fournir des informations exactes (prix, localisation, caractéristiques)</li>
          <li>publier des vidéos et photos authentiques correspondant au bien décrit</li>
          <li>retirer ou mettre à jour les annonces dès qu'un bien n'est plus disponible</li>
          <li>éviter toute publicité trompeuse</li>
        </ul>
      </section>

      <section>
        <h2>4. Responsabilité des contenus</h2>
        <p>L'agent est <strong>seul responsable</strong> :</p>
        <ul>
          <li>des biens publiés sur la plateforme</li>
          <li>des informations fournies aux utilisateurs</li>
          <li>des relations commerciales avec les clients</li>
        </ul>
        <p>Monajent ne garantit pas la véracité des contenus publiés par les agents et ne saurait être tenu responsable en cas de litige entre un agent et un utilisateur.</p>
      </section>

      <section>
        <h2>5. Gratuité et évolution du modèle</h2>
        <p>À la date des présentes conditions, <strong>l'utilisation de Monajent est entièrement gratuite pour les agents</strong>. La création de compte, la publication d'annonces (vidéos, photos, descriptions) et l'accès à l'ensemble des fonctionnalités ne font l'objet d'aucun frais.</p>
        <p>Monajent est actuellement dans une phase de développement stratégique visant à construire un écosystème innovant pour la recherche immobilière en Côte d'Ivoire. Durant cette phase, la priorité est donnée à la qualité du service et à l'expérience utilisateur.</p>
        <p>Le modèle économique est susceptible d'évoluer. Monajent pourra introduire, à l'avenir, des fonctionnalités premium payantes pour les agents (mise en avant d'annonces, outils d'analyse avancés, services de promotion, système de rémunération sur les vues, etc.). <strong>Les agents seront informés de tout changement avant sa mise en application.</strong></p>
      </section>

      <section>
        <h2>6. Visites physiques</h2>
        <p>L'agent s'engage à :</p>
        <ul>
          <li>assurer les visites programmées via la plateforme dans les délais convenus</li>
          <li>confirmer ou décliner les demandes de visite dans un délai de 48 heures</li>
          <li>respecter les engagements pris avec les utilisateurs</li>
          <li>se présenter au rendez-vous ou prévenir en cas d'empêchement</li>
        </ul>
      </section>

      <section>
        <h2>7. Comportement attendu</h2>
        <p>Il est strictement interdit de :</p>
        <ul>
          <li>publier de faux biens ou des annonces trompeuses</li>
          <li>escroquer les utilisateurs de la plateforme</li>
          <li>harceler ou manquer de respect envers les utilisateurs</li>
          <li>utiliser la plateforme à des fins contraires à son objet</li>
        </ul>
      </section>

      <section>
        <h2>8. Suspension et résiliation</h2>
        <p>Monajent peut suspendre ou résilier le compte d'un agent en cas de :</p>
        <ul>
          <li>fraude avérée ou tentative de fraude</li>
          <li>plaintes répétées de la part des utilisateurs</li>
          <li>publication de contenus trompeurs ou frauduleux</li>
          <li>non-respect des présentes conditions</li>
          <li>inactivité prolongée sans justification</li>
        </ul>
      </section>

      <section>
        <h2>9. Protection des données des agents</h2>
        <p>Les pièces d'identité et informations personnelles des agents sont :</p>
        <ul>
          <li>utilisées <strong>uniquement</strong> pour la vérification du profil</li>
          <li>stockées de manière sécurisée avec accès restreint</li>
          <li>jamais partagées avec des tiers sans consentement</li>
        </ul>
        <p>Pour plus de détails, consultez notre <router-link to="/legal/confidentialite">Politique de Confidentialité</router-link>.</p>
      </section>

      <section>
        <h2>10. Évolution du service</h2>
        <p>Monajent est un service en constante évolution. De nouvelles fonctionnalités, outils et services pourront être ajoutés, modifiés ou retirés. Le modèle économique, les conditions d'utilisation et les fonctionnalités applicables aux agents sont susceptibles d'évoluer dans le cadre du développement de la plateforme.</p>
        <p><strong>Les agents seront informés de tout changement significatif avec un préavis raisonnable.</strong></p>
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
.legal-content a { color: #1DA53F; text-decoration: none; }
.legal-content a:hover { text-decoration: underline; }
@media (max-width: 600px) {
  .legal-content h1 { font-size: 22px; }
  .legal-content { padding: 24px 16px 60px; }
}
</style>
