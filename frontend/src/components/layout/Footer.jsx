import React from "react";
import styles from "./Footer.module.css";

const Footer = () => {
  const year = new Date().getFullYear();

  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <p className={styles.text}>
          © {year} PriceCompare. All rights reserved.
        </p>
        <p className={styles.secondary}>
          Built for fast, transparent price discovery.
        </p>
      </div>
    </footer>
  );
};

export default Footer;

