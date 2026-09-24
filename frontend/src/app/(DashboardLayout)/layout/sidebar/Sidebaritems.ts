import { uniqueId } from 'lodash';

export interface ChildItem {
  id?: number | string;
  name?: string;
  icon?: any;
  children?: ChildItem[];
  item?: any;
  url?: any;
  color?: string;
  disabled?: boolean;
  subtitle?: string;
  badge?: boolean;
  badgeType?: string;
  isPro?: boolean;
}

export interface MenuItem {
  heading?: string;
  name?: string;
  icon?: any;
  id?: number | string;
  to?: string;
  items?: MenuItem[];
  children?: ChildItem[];
  url?: any;
  disabled?: boolean;
  subtitle?: string;
  badgeType?: string;
  badge?: boolean;
  isPro?: boolean;
}

const SidebarContent: MenuItem[] = [
  {
    heading: 'MiniUI Platform',
    children: [
      {
        name: 'Dashboard',
        icon: 'solar:widget-2-linear',
        id: uniqueId(),
        url: '/',
        isPro: false,
      },
      {
        name: 'Applications',
        icon: 'solar:layers-line-duotone',
        id: uniqueId(),
        url: '/apps',
        isPro: false,
      },
      {
        name: 'New Application',
        icon: 'solar:document-add-linear',
        id: uniqueId(),
        url: '/apps/new',
        isPro: false,
      },
    ],
  },
  {
    heading: 'Design & Templates',
    children: [
      {
        name: 'UI Components',
        icon: 'solar:widget-6-outline',
        id: uniqueId(),
        url: '/utilities/form',
        isPro: false,
      },
      {
        name: 'Typography',
        icon: 'solar:text-circle-outline',
        id: uniqueId(),
        url: '/utilities/typography',
        isPro: false,
      },
      {
        name: 'Tables',
        icon: 'solar:server-linear',
        id: uniqueId(),
        url: '/utilities/table',
        isPro: false,
      },
    ],
  },
];

export default SidebarContent;
