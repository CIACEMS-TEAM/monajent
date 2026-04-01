<script setup lang="ts">
import logoUrl from '@/assets/icons/logo_monajent_header.png'
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
      <p class="legal-meta">Dernière mise à jour : 31 mars 2026 — Version 2026-03-31-v1</p>

      <section>
        <h2>1. Objet</h2>
        <p>Les présentes Conditions Générales d'Utilisation (CGU) ont pour objet de définir les modalités d'accès et d'utilisation de la plateforme Monajent, application de mise en relation entre agents immobiliers et utilisateurs à la recherche de biens immobiliers.</p>
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
          <li>aux agents immobiliers souhaitant publier des biens</li>
          <li>aux utilisateurs (clients) souhaitant consulter des biens</li>
        </ul>
        <p>L'accès peut nécessiter la création d'un compte.</p>
      </section>

      <section>
        <h2>4. Description du service</h2>
        <p>Monajent permet :</p>
        <ul>
          <li>la publication de vidéos de biens immobiliers</li>
          <li>l'accès payant à des contenus (vidéos)</li>
          <li>la mise en relation entre utilisateurs et agents</li>
          <li>l'organisation de visites physiques gratuites (selon le modèle proposé)</li>
        </ul>
        <p><strong>Monajent n'est pas une agence immobilière</strong> et n'intervient pas dans la transaction finale entre les parties.</p>
      </section>

      <section>
        <h2>5. Inscription des agents</h2>
        <p>Les agents doivent fournir :</p>
        <ul>
          <li>des informations exactes</li>
          <li>une pièce d'identité valide</li>
          <li>des contenus authentiques</li>
        </ul>
        <p>Monajent se réserve le droit de refuser ou suspendre un compte, et de supprimer tout contenu frauduleux.</p>
      </section>

      <section>
        <h2>6. Engagement des utilisateurs</h2>
        <p>L'utilisateur s'engage à :</p>
        <ul>
          <li>utiliser la plateforme de manière légale</li>
          <li>ne pas frauder ou détourner le service</li>
          <li>respecter les autres utilisateurs</li>
        </ul>
      </section>

      <section>
        <h2>7. Paiements</h2>
        <p>Certains contenus (vidéos) peuvent être accessibles contre paiement. Les paiements donnent accès à :</p>
        <ul>
          <li>des vidéos de biens immobiliers</li>
          <li>des visites physiques gratuites (selon conditions)</li>
        </ul>
        <p><strong>Les paiements ne garantissent pas la disponibilité du bien ni la conclusion d'une transaction.</strong></p>
      </section>

      <section>
        <h2>8. Responsabilité</h2>
        <p>Monajent :</p>
        <ul>
          <li>n'est pas responsable de la véracité totale des biens publiés</li>
          <li>n'est pas responsable des transactions entre utilisateurs et agents</li>
          <li>agit comme plateforme intermédiaire</li>
        </ul>
        <p>Les agents sont seuls responsables des biens qu'ils publient.</p>
      </section>

      <section>
        <h2>9. Suspension / Résiliation</h2>
        <p>Monajent peut suspendre ou supprimer un compte en cas de fraude, fausse information, ou non-respect des CGU.</p>
      </section>

      <section>
        <h2>10. Modification des CGU</h2>
        <p>Monajent se réserve le droit de modifier les CGU à tout moment. Les utilisateurs seront informés en cas de changement.</p>
      </section>

      <section>
        <h2>11. Droit applicable</h2>
        <p>Les présentes CGU sont régies par le droit ivoirien.</p>
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
