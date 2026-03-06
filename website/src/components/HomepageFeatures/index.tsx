import React from 'react';
import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  Svg: React.ComponentType<React.ComponentProps<'svg'>>;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Cognitive Modeling (BKT)',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        Utilizes <strong>Bayesian Knowledge Tracing</strong> to probabilistically estimate student mastery. 
        The system differentiates between slips, guesses, and true learning, ensuring that the difficulty curve adapts in real-time.
      </>
    ),
  },
  {
    title: 'Neuro-Symbolic Architecture',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        Combines the generative power of <strong>LLMs (Llama 3.1)</strong> with the structured precision of <strong>Knowledge Graphs</strong>.
        This ensures pedagogical accuracy while maintaining natural, empathetic dialogue.
      </>
    ),
  },
  {
    title: 'Spaced Repetition (SRS)',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        Implements the <strong>Ebbinghaus Forgetting Curve</strong> to schedule reviews at optimal intervals.
        The system predicts memory decay and reinforces concepts exactly when the student is about to forget them.
      </>
    ),
  },
];

function Feature({title, Svg, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
