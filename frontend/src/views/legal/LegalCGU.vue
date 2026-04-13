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
      <h1>Conditions Générales d'Utilisation (CGU)</h1>
      <p class="legal-meta">Dernière mise à jour : 13 avril 2026 — Version 2026-04-13-v2</p>

      <section>
        <h2>1. Objet</h2>
        <p>Les présentes Conditions Générales d'Utilisation (CGU) ont pour objet de définir les modalités d'accès et d'utilisation de la plateforme Monajent, application de mise en relation entre agents immobiliers et utilisateurs à la recherche de biens immobiliers en Côte d'Ivoire.</p>
        <p>Monajent a pour ambition de <strong>révolutionner la recherche immobilière en Côte d'Ivoire</strong> en offrant un outil moderne et innovant aux agents immobiliers et une expérience unique aux usagers.</p>
      </section>

      <section>
        <h2>2. Éditeur de la plateforme</h2>
        <p>La plateforme Monajent est éditée par :</p>
        <ul>
          <li><strong>CIACEMS</strong></li>
          <li>Email : itciacems@gmail.com</li>
          <li>Téléphone : +225 27 22 30 08 40</li>
        </ul>
      </section>

      <section>
        <h2>3. Accès à la plateforme</h2>
        <p>La plateforme est accessible :</p>
        <ul>
          <li>aux <strong>agents immobiliers</strong> souhaitant publier et promouvoir des biens</li>
          <li>aux <strong>utilisateurs (clients)</strong> souhaitant rechercher et consulter des biens</li>
        </ul>
        <p>L'inscription est <strong>gratuite</strong> pour les agents comme pour les clients. La consultation des vidéos et photos des annonces nécessite la création d'un compte gratuit.</p>
      </section>

      <section>
        <h2>4. Description du service</h2>
        <p>Monajent permet :</p>
        <ul>
          <li>la publication de vidéos et photos de biens immobiliers par les agents</li>
          <li>la recherche de biens par intelligence artificielle (assistante Mona)</li>
          <li>l'accès gratuit aux vidéos et photos pour les utilisateurs connectés</li>
          <li>la mise en relation entre utilisateurs et agents</li>
          <li>la programmation de visites physiques</li>
        </ul>
        <p><strong>Monajent n'est pas une agence immobilière</strong> et n'intervient pas dans la transaction finale entre les parties.</p>
      </section>

      <section>
        <h2>5. Inscription des agents</h2>
        <p>Les agents doivent fournir :</p>
        <ul>
          <li>des informations exactes et vérifiables</li>
          <li>une pièce d'identité valide</li>
          <li>des contenus authentiques représentant des biens réels</li>
        </ul>
        <p>Monajent se réserve le droit de refuser ou suspendre un compte, et de supprimer tout contenu frauduleux.</p>
      </section>

      <section>
        <h2>6. Engagement des utilisateurs</h2>
        <p>L'utilisateur s'engage à :</p>
        <ul>
          <li>utiliser la plateforme de manière légale et conforme à son objet</li>
          <li>ne pas frauder, contourner ou détourner le service</li>
          <li>respecter les autres utilisateurs et les agents</li>
          <li>ne pas télécharger, copier ou redistribuer les contenus (vidéos, photos) publiés sur la plateforme</li>
        </ul>
      </section>

      <section>
        <h2>7. Gratuité et évolution du modèle</h2>
        <p>À la date des présentes CGU, <strong>l'ensemble des services Monajent est accessible gratuitement</strong>, tant pour les agents que pour les utilisateurs. L'inscription, la publication d'annonces, la consultation des vidéos et photos, ainsi que la programmation de visites sont entièrement gratuites.</p>
        <p>Monajent se réserve le droit de faire évoluer son modèle économique et d'introduire, à l'avenir, des fonctionnalités ou services payants (abonnements premium, options de mise en avant, services à valeur ajoutée, etc.). <strong>Les utilisateurs seront informés de tout changement avant sa mise en application.</strong></p>
        <p>L'utilisation des services gratuits ne crée aucun droit acquis à la gratuité permanente desdits services.</p>
      </section>

      <section>
        <h2>8. Responsabilité</h2>
        <p>Monajent :</p>
        <ul>
          <li>n'est pas responsable de la véracité des biens publiés par les agents</li>
          <li>n'est pas responsable des transactions entre utilisateurs et agents</li>
          <li>agit comme plateforme intermédiaire de mise en relation</li>
        </ul>
        <p>Les agents sont seuls responsables des biens qu'ils publient et des engagements qu'ils prennent envers les utilisateurs.</p>
      </section>

      <section>
        <h2>9. Propriété intellectuelle</h2>
        <p>L'ensemble des éléments de la plateforme (design, logo, code, fonctionnalités, assistante IA Mona) est la propriété exclusive de CIACEMS. Les contenus publiés par les agents restent leur propriété, mais ils accordent à Monajent une licence d'utilisation dans le cadre du service.</p>
      </section>

      <section>
        <h2>10. Suspension / Résiliation</h2>
        <p>Monajent peut suspendre ou supprimer un compte en cas de fraude, fausse information, abus ou non-respect des CGU.</p>
      </section>

      <section>
        <h2>11. Modification des CGU</h2>
        <p>Monajent se réserve le droit de modifier les présentes CGU à tout moment, notamment pour refléter l'évolution du service et de son modèle économique. Les utilisateurs seront informés de toute modification significative.</p>
      </section>

      <section>
        <h2>12. Droit applicable</h2>
        <p>Les présentes CGU sont régies par le droit ivoirien. Tout litige sera soumis aux juridictions compétentes d'Abidjan.</p>
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
