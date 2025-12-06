/**
 * Centralized Icon exports from Tabler Icons
 * Usage: import { IconChart, IconTarget } from '../components/Icons';
 */
export {
    // Navigation & UI
    IconHome,
    IconMenu2,
    IconX,
    IconChevronDown,
    IconChevronRight,
    IconChevronLeft,
    IconArrowRight,
    IconArrowLeft,
    IconExternalLink,

    // Match & Game
    IconSwords,
    IconTrophy,
    IconTarget,
    IconCrown,
    IconFlame,
    IconBolt,
    IconShield,
    IconSkull,

    // Analytics & Data
    IconChartBar,
    IconChartLine,
    IconChartPie,
    IconChartArrowsVertical,
    IconTrendingUp,
    IconTrendingDown,
    IconPercentage,
    IconGraph,

    // AI & ML
    IconBrain,
    IconCpu,
    IconRobot,
    IconSparkles,
    IconWand,

    // Status & Indicators
    IconCircleCheck,
    IconCircleX,
    IconAlertCircle,
    IconAlertTriangle,
    IconInfoCircle,
    IconClock,
    IconCalendar,
    IconLive,
    IconEye,
    IconUsers,

    // Communication
    IconMessage,
    IconMail,
    IconBrandDiscord,
    IconBrandTwitter,
    IconHeartFilled,
    IconHeart,
    IconBug,
    IconBulb,
    IconMessageCircle,
    IconSend,

    // Money & Betting
    IconCoin,
    IconWallet,
    IconScale,
    IconCash,

    // Content
    IconBook,
    IconFileText,
    IconClipboardList,
    IconQuestionMark,
    IconCheck,
    IconRefresh,
    IconDownload,
    IconDatabase,

    // Team & Players
    IconUser,
    IconUserCircle,
    IconUsersGroup,
    IconStar,
    IconPlayerPlay,
} from '@tabler/icons-react';

// Custom color variants for common icons
export const LiveDot = ({ className = '' }: { className?: string }) => (
    <span className={`inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse ${className}`} />
);

// Icon sizes for consistency
export const iconSizes = {
    sm: 16,
    md: 20,
    lg: 24,
    xl: 32,
    '2xl': 48,
};
