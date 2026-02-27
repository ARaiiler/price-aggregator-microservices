const User = require('../models/User');
const express = require('express');
const jwt = require('jsonwebtoken');
const router = express.Router();

// POST /auth/register
router.post('/register', async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        error: { message: 'Email and password are required', status: 400 }
      });
    }

    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(400).json({
        error: { message: 'Email already in use', status: 400 }
      });
    }

    const user = await User.create({ email, password });

    res.status(201).json({
      message: 'User registered successfully',
      user: { id: user._id, email: user.email }
    });

  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({
      error: { message: 'Registration failed', status: 500 }
    });
  }
});

// POST /auth/login
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        error: { message: 'Email and password are required', status: 400 }
      });
    }

    const user = await User.findOne({ email });
    if (!user) {
      return res.status(401).json({
        error: { message: 'Invalid credentials', status: 401 }
      });
    }

    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      return res.status(401).json({
        error: { message: 'Invalid credentials', status: 401 }
      });
    }

    const token = jwt.sign(
      { userId: user._id, email: user.email },
      process.env.JWT_SECRET,
      { expiresIn: '24h' }
    );

    // ✅ Retourner aussi "user" pour que le frontend puisse le stocker
    res.status(200).json({
      message: 'Login successful',
      token,
      expiresIn: '24h',
      user: {
        id: user._id,
        email: user.email,
        role: user.role,
      }
    });

  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({
      error: { message: 'Login failed', status: 500 }
    });
  }
});

module.exports = router;