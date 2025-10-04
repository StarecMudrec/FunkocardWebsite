// src/api/index.js
import axios from 'axios'


// Fetch cards for a specific season
export async function fetchCardsForSeason(seasonId, sortField = 'id', sortDirection = 'asc') {
  try {
    const response = await axios.get(`/api/cards/${seasonId}`, {
      params: {
        sort: sortField,
        direction: sortDirection
      }
    });
    
    // Transform the data to match what your Card component expects
    return response.data.map(card => ({
      id: card.id,
      uuid: card.uuid || card.id.toString(), // Fallback to id if uuid doesn't exist
      img: card.photo || card.img,           // Handle different field names
      name: card.name,
      rarity: card.rarity,
      points: card.points,
      category: card.rarity,                 // Map rarity to category if needed
      // Include any other required fields
    }));
    
  } catch (error) {
    console.error('Error fetching cards:', error);
    throw error;
  }
}

// Fetch detailed card info
export const fetchCardInfo = async (cardId) => {
  const response = await fetch(`/api/card_info/${cardId}`)
  if (!response.ok) throw new Error('Failed to fetch card info')
  return response.json()
}

// Fetch all categories
export const fetchCategories = async () => {
  try {
    const response = await fetch('/api/categories');
    if (!response.ok) throw new Error('Failed to fetch categories');
    return await response.json();
  } catch (error) {
    console.error('Error fetching categories:', error);
    throw error;
  }
}

// Fetch comments for a card
export const fetchComments = async (cardId) => {
  const response = await fetch(`/api/comments/${cardId}`)
  if (!response.ok) throw new Error('Failed to fetch comments')
  return response.json()
}

export const checkAuth = async () => {
  try {
    const response = await fetch('/api/check_auth')
    if (!response.ok) throw new Error('Auth check failed')
    return await response.json()
  } catch (error) {
    console.error('Auth check error:', error)
    return { isAuthenticated: false, userId: null }
  }
} 

// Check user permission
export const checkUserPermission = async (username) => {
  try {
    const response = await fetch(`/api/check_permission?username=${username}`);
    if (!response.ok) throw new Error('Permission check failed');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Permission check error:', error);
    return false; // Assume not allowed on error
  }
};

// Fetch user information
export const fetchUserInfo = async () => {
  const response = await fetch('/api/user');
  if (!response.ok) throw new Error('Failed to fetch user info');
  return response.json();
};