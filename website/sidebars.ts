import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Core Architecture',
      collapsible: false,
      items: [
        'architecture/overview',
        'architecture/knowledge-engine',
        'architecture/pedagogy-engine',
        'architecture/learner-engine',
        'architecture/tutor-engine',
        'architecture/assessment-engine',
      ],
    },
    {
      type: 'category',
      label: 'Technical Reference',
      collapsible: false,
      items: [
        'technical/auth',
        'technical/database',
        'technical/api',
        'technical/testing',
      ],
    },
  ],
};

export default sidebars;
