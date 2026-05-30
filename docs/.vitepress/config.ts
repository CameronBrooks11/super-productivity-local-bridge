import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'SP Local Bridge',
  description: 'Control Super Productivity from MCP hosts, CLI, and automation tools',
  base: '/super-productivity-local-bridge/',

  head: [
    ['meta', { name: 'theme-color', content: '#00796b' }],
  ],

  themeConfig: {
    nav: [
      { text: 'Guide', link: '/getting-started' },
      { text: 'Operations', link: '/operations' },
      { text: 'GitHub', link: 'https://github.com/CameronBrooks11/super-productivity-local-bridge' },
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
      message: 'Released under the MIT License.',
    },
  },
})
