import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'SP Local Bridge (Python)',
  description: 'Legacy Python bridge for Super Productivity — superseded by the Go bridge.',
  base: '/super-productivity-local-bridge/',

  head: [
    ['meta', { name: 'theme-color', content: '#00796b' }],
  ],

  themeConfig: {
    siteTitle: 'SP Bridge (Python)',

    nav: [
      { text: '⚡ Go Bridge (recommended)', link: 'https://cameronbrooks11.github.io/super-productivity-local-gobridge/' },
      { text: 'Guide', link: '/getting-started' },
      { text: 'Operations', link: '/operations' },
    ],

    sidebar: [
      {
        text: 'Start',
        items: [
          { text: 'Getting Started', link: '/getting-started' },
          { text: 'Security', link: '/security' },
        ],
      },
      {
        text: 'Host Setup',
        items: [
          { text: 'Overview', link: '/hosts/' },
          { text: 'VS Code Copilot', link: '/hosts/vscode-copilot' },
          { text: 'Claude Desktop', link: '/hosts/claude-desktop' },
          { text: 'Codex', link: '/hosts/codex' },
        ],
      },
      {
        text: 'Reference',
        items: [
          { text: 'Operations', link: '/operations' },
          { text: 'Architecture', link: '/architecture' },
          { text: 'Troubleshooting', link: '/troubleshooting' },
        ],
      },
      {
        text: 'Project',
        items: [
          { text: 'Validation', link: '/validation' },
        ],
      },
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/CameronBrooks11/super-productivity-local-bridge' },
    ],

    search: {
      provider: 'local',
    },

    footer: {
      message: 'Released under the MIT License. New users: use the <a href="https://cameronbrooks11.github.io/super-productivity-local-gobridge/">Go bridge</a>.',
    },
  },
})
