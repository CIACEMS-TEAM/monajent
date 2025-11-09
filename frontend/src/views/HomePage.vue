<template>
    <div class="monajent-container">
      <!-- Header -->
      <header class="header">
        <div class="header-top">
          <div class="header-contact">
            <span>Appelez-nous (+34) 933 562 989</span>
          </div>
          <div class="header-links">
            <a href="#about">Qui sommes-nous</a>
            <a href="#services">Services</a>
            <span class="language">Français</span>
            <a href="#search" class="search-link">Rechercher une propriété</a>
            <a href="#account">MyMonaJent</a>
          </div>
        </div>
  
        <nav class="navbar">
          <div class="logo-container">
            <img src="/logo-monajent.png" alt="MonaJent" class="logo">
            <span class="company-name">MonaJent</span>
          </div>
          <ul class="nav-menu">
            <li><a href="#buy">Acheter</a></li>
            <li><a href="#rent">Louer</a></li>
            <li><a href="#sell">Vendre</a></li>
            <li><a href="#constructions">Constructions</a></li>
            <li><a href="#sites">Sites</a></li>
            <li><a href="#contact">Contacter</a></li>
          </ul>
        </nav>
      </header>
  
      <!-- Hero Section -->
      <section class="hero">
        <div class="hero-overlay"></div>
        <div class="hero-content">
          <h1>PROPRIÉTÉS EXCLUSIVES EN ESPAGNE, PORTUGAL, FRANCE ET ANDORRE</h1>
          
        <div class="tabs">
            <button class="tab-button active">Propriétés</button>
            <button class="tab-button">Référence</button>
          </div>
  
          <!-- Search Form -->
          <div class="search-form">
            <div class="form-group">
              <label>Vous recherchez...</label>
              <select class="form-select">
                <option>Acheter</option>
                <option>Louer</option>
              </select>
            </div>
            <div class="form-group">
              <label>Localité</label>
              <input type="text" class="form-input" placeholder="Indiquez votre localité">
            </div>
            <button class="search-button">Recherche</button>
          </div>

          <!-- CTA Auth -->
          <div class="cta-auth">
            <router-link class="cta primary" to="/auth/join">Créer un compte</router-link>
            <router-link class="cta secondary" to="/auth/login">Se connecter</router-link>
          </div>
        </div>
      </section>
  
      <!-- Featured Locations -->
      <section class="locations-section">
        <h2>Consultez nos localités mises en vedette</h2>
        <p class="section-subtitle">Chez MonaJent, nous propositions à nos clients les meilleures propriétés de luxe d'Espagne</p>
        
        <div class="locations-grid">
          <div class="location-card">
            <div class="location-image andorre"></div>
            <h3>ANDORRE</h3>
          </div>
          <div class="location-card">
            <div class="location-image barcelone"></div>
            <h3>BARCELONE</h3>
          </div>
          <div class="location-card">
            <div class="location-image costa"></div>
            <h3>COSTA BRAVA</h3>
          </div>
        </div>
      </section>
  
      <!-- Properties Grid -->
      <section class="properties-section">
        <h2>Propriétés résidentielles à Barcelone</h2>
        
        <div class="properties-grid">
          <div class="property-card" v-for="property in properties" :key="property.id">
            <div class="property-image">
              <img :src="property.image" :alt="property.title">
              <span class="exclusive-badge">Listing Exclusif</span>
              <button class="like-button" @click="toggleLike(property.id)">
                <span v-if="property.liked">❤</span>
                <span v-else>🤍</span>
              </button>
            </div>
            <div class="property-info">
              <p class="property-status">{{ property.status }}</p>
              <p class="property-price">{{ property.price }}</p>
              <p class="property-location">{{ property.location }}</p>
              <p class="property-title">{{ property.title }}</p>
              <div class="property-details">
                <div class="detail-item">
                  <span class="detail-number">{{ property.bedrooms }}</span>
                  <span class="detail-label">Chambres</span>
                </div>
                <div class="detail-item">
                  <span class="detail-number">{{ property.bathrooms }}</span>
                  <span class="detail-label">Salles de bains</span>
                </div>
                <div class="detail-item">
                  <span class="detail-number">{{ property.area }}</span>
                  <span class="detail-label">Plan</span>
                </div>
                <div class="detail-item" v-if="property.terrace">
                  <span class="detail-number">{{ property.terrace }}</span>
                  <span class="detail-label">Terrasse</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  
  const properties = ref([
    {
      id: 1,
      status: 'À vendre, Appartement',
      price: '660 000 €',
      location: 'Barcelone, Sitges, Sitges Town / Sant Sebastian / Aiguadolç',
      title: 'Appartement de 77m² à vendre à Sitges Town, Barcelone',
      bedrooms: '2',
      bathrooms: '1',
      area: '77m²',
      terrace: '5m²',
      image: '/placeholder.svg?height=300&width=300',
      liked: false
    },
    {
      id: 2,
      status: 'À vendre, Appartement',
      price: '590 000 €',
      location: 'Barcelone, Sant Just Desvern',
      title: 'Appartement de 106m² à vendre à Sant Just, Barcelone',
      bedrooms: '3',
      bathrooms: '2',
      area: '106m²',
      terrace: null,
      image: '/placeholder.svg?height=300&width=300',
      liked: false
    },
    {
      id: 3,
      status: 'À vendre, Appartement',
      price: '530 000 €',
      location: 'Barcelone, Barcelone ville, Eixample Gauche',
      title: 'Appartement de 68m² à vendre à Eixample Gauche avec 10m² terrasse',
      bedrooms: '2',
      bathrooms: '2',
      area: '68m²',
      terrace: '10m²',
      image: '/placeholder.svg?height=300&width=300',
      liked: false
    }
  ])
  
  const toggleLike = (id) => {
    const property = properties.value.find(p => p.id === id)
    if (property) {
      property.liked = !property.liked
    }
  }
  </script>
  
  <style scoped>
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  
  .monajent-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    color: #333;
  }
  
  /* Header Styles */
  .header {
    background-color: #fff;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }
  
  .header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 40px;
    font-size: 13px;
    border-bottom: 1px solid #f0f0f0;
  }
  
  .header-contact {
    color: #666;
  }
  
  .header-links {
    display: flex;
    gap: 30px;
    align-items: center;
  }
  
  .header-links a {
    text-decoration: none;
    color: #333;
    font-size: 13px;
    transition: color 0.3s;
  }
  
  .header-links a:hover {
    color: #27ae60;
  }
  
  .language {
    color: #999;
  }
  
  .search-link {
    color: #27ae60;
    font-weight: 600;
  }
  
  .navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 40px;
  }
  
  .logo-container {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .logo {
    height: 50px;
    width: auto;
  }
  
  .company-name {
    font-size: 20px;
    font-weight: 700;
    color: #333;
  }
  
  .nav-menu {
    display: flex;
    list-style: none;
    gap: 30px;
  }
  
  .nav-menu a {
    text-decoration: none;
    color: #333;
    font-size: 14px;
    font-weight: 500;
    transition: color 0.3s;
  }
  
  .nav-menu a:hover {
    color: #27ae60;
  }
  
  /* Hero Section */
  .hero {
    position: relative;
    height: 500px;
    background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), 
                url('/placeholder.svg?height=500&width=1200') center/cover;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: white;
    text-align: center;
  }
  
  .hero-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.35);
  }
  
  .hero-content {
    position: relative;
    z-index: 2;
    max-width: 1000px;
    width: 100%;
  }
  
  .hero h1 {
    font-size: 36px;
    font-weight: 700;
    margin-bottom: 30px;
    line-height: 1.3;
    letter-spacing: 0.5px;
  }
  
  .tabs {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-bottom: 40px;
  }
  
  .tab-button {
    background: none;
    border: none;
    color: white;
    font-size: 16px;
    cursor: pointer;
    padding-bottom: 10px;
    border-bottom: 3px solid transparent;
    transition: border-color 0.3s;
  }
  
  .tab-button.active {
    border-bottom-color: white;
  }
  
  .tab-button:hover {
    opacity: 0.8;
  }
  
  .search-form {
    display: flex;
    gap: 20px;
    justify-content: center;
    align-items: flex-end;
    padding: 0 20px;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }
  
  .form-group label {
    color: #fff;
    font-size: 13px;
    margin-bottom: 8px;
    font-weight: 500;
  }
  
  .form-select,
  .form-input {
    padding: 12px 15px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    min-width: 200px;
    background: white;
    color: #333;
  }
  
  .form-select {
    cursor: pointer;
    appearance: none;
    background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
    background-repeat: no-repeat;
    background-position: right 10px center;
    background-size: 20px;
    padding-right: 35px;
  }
  
  .form-input::placeholder {
    color: #999;
  }
  
  .search-button {
    padding: 12px 30px;
    background-color: #1a3a2a;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.3s;
  }
  
  .search-button:hover {
    background-color: #27ae60;
  }
  .cta-auth { margin-top: 24px; display:flex; gap: 12px; justify-content: center; }
  .cta { text-decoration:none; padding: 10px 16px; border-radius: 8px; font-weight:600; }
  .cta.primary { background:#1a3a2a; color:#fff; }
  .cta.secondary { background:#ffffff; color:#1a3a2a; border:1px solid #ddd; }
  
  /* Locations Section */
  .locations-section {
    padding: 60px 40px;
    background-color: #f9f9f9;
    text-align: center;
  }
  
  .locations-section h2 {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 15px;
    color: #333;
  }
  
  .section-subtitle {
    font-size: 15px;
    color: #666;
    margin-bottom: 40px;
    line-height: 1.6;
  }
  
  .locations-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 30px;
    max-width: 1200px;
    margin: 0 auto;
  }
  
  .location-card {
    position: relative;
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.3s;
  }
  
  .location-card:hover {
    transform: translateY(-5px);
  }
  
  .location-image {
    width: 100%;
    height: 250px;
    background-size: cover;
    background-position: center;
    position: relative;
  }
  
  .location-card h3 {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(to top, rgba(0, 0, 0, 0.7), transparent);
    color: white;
    padding: 30px 20px 20px;
    font-size: 18px;
    font-weight: 700;
  }
  
  .location-image.andorre {
    background: linear-gradient(135deg, #8B7355, #D2B48C);
  }
  
  .location-image.barcelone {
    background: linear-gradient(135deg, #C9A961, #E8D5B7);
  }
  
  .location-image.costa {
    background: linear-gradient(135deg, #20B2AA, #87CEEB);
  }
  
  /* Properties Section */
  .properties-section {
    padding: 60px 40px;
    max-width: 1400px;
    margin: 0 auto;
  }
  
  .properties-section h2 {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 40px;
    color: #333;
    text-align: center;
  }
  
  .properties-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 30px;
  }
  
  .property-card {
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: box-shadow 0.3s, transform 0.3s;
  }
  
  .property-card:hover {
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
    transform: translateY(-3px);
  }
  
  .property-image {
    position: relative;
    height: 250px;
    overflow: hidden;
    background: #e0e0e0;
  }
  
  .property-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s;
  }
  
  .property-card:hover .property-image img {
    transform: scale(1.05);
  }
  
  .exclusive-badge {
    position: absolute;
    top: 15px;
    left: 15px;
    background-color: #1a3a2a;
    color: white;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    z-index: 1;
  }
  
  .like-button {
    position: absolute;
    top: 15px;
    right: 15px;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 1px solid white;
    background-color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    transition: all 0.3s;
  }
  
  .like-button:hover {
    background-color: #f0f0f0;
  }
  
  .property-info {
    padding: 20px;
  }
  
  .property-status {
    font-size: 12px;
    color: #999;
    margin-bottom: 8px;
    text-transform: uppercase;
  }
  
  .property-price {
    font-size: 22px;
    font-weight: 700;
    color: #333;
    margin-bottom: 8px;
  }
  
  .property-location {
    font-size: 12px;
    color: #999;
    margin-bottom: 8px;
  }
  
  .property-title {
    font-size: 14px;
    color: #333;
    margin-bottom: 15px;
    line-height: 1.5;
    font-weight: 500;
  }
  
  .property-details {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    padding-top: 15px;
    border-top: 1px solid #f0f0f0;
  }
  
  .detail-item {
    text-align: center;
  }
  
  .detail-number {
    display: block;
    font-size: 14px;
    font-weight: 700;
    color: #333;
  }
  
  .detail-label {
    display: block;
    font-size: 11px;
    color: #999;
    margin-top: 4px;
  }
  
  /* Responsive Design */
  @media (max-width: 1024px) {
    .properties-grid,
    .locations-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  
    .search-form {
      flex-direction: column;
      align-items: stretch;
    }
  
    .form-select,
    .form-input {
      min-width: 100%;
    }
  }
  
  @media (max-width: 768px) {
    .header-top {
      flex-direction: column;
      gap: 10px;
      padding: 10px 20px;
    }
  
    .navbar {
      flex-direction: column;
      gap: 15px;
      padding: 15px 20px;
    }
  
    .nav-menu {
      flex-direction: column;
      gap: 15px;
      width: 100%;
    }
  
    .nav-menu a {
      display: block;
    }
  
    .hero h1 {
      font-size: 24px;
    }
  
    .properties-grid,
    .locations-grid {
      grid-template-columns: 1fr;
    }
  
    .property-details {
      grid-template-columns: repeat(2, 1fr);
    }
  
    .search-form {
      flex-direction: column;
    }
  }
  </style>
  