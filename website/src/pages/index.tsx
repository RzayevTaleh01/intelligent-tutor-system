import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/intro">
            Read the Tutorial
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home(): JSX.Element {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`Welcome to ${siteConfig.title}`}
      description="Next-Generation Intelligent Tutoring System driven by Neuro-Symbolic AI and Cognitive Modeling">
      <HomepageHeader />
      <main>
        <div className="container padding-vert--xl">
          <div className="row">
            <div className="col col--8 col--offset-2 text--center">
              <h2>A Paradigm Shift in Adaptive Education</h2>
              <p className="text--lg">
                EduVision ITS represents a novel approach to personalized learning, moving beyond static rule-based systems to a fully dynamic, cognitive architecture. By synthesizing <strong>Bayesian Knowledge Tracing (BKT)</strong>, <strong>Spaced Repetition Systems (SRS)</strong>, and <strong>Large Language Models (LLMs)</strong>, we create a digital tutor that truly understands the learner.
              </p>
            </div>
          </div>
        </div>
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
