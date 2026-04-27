import type { ReactNode } from "react";

import {
  AppstoreOutlined,
  FileSearchOutlined,
  HomeOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MessageOutlined,
  TeamOutlined
} from "@ant-design/icons";
import { Button, Layout, Menu } from "antd";
import { motion } from "framer-motion";
import dayjs from "dayjs";
import { Link, Outlet, useLocation } from "react-router-dom";

import { useLayoutStore } from "../../stores/layoutStore";

const { Header, Sider, Content } = Layout;

type SectionMeta = {
  key: string;
  icon: ReactNode;
  navLabel: string;
  navNote: string;
  headerTag: string;
  headerTitle: string;
  headerNote: string;
};

const sectionItems: SectionMeta[] = [
  {
    key: "/dashboard",
    icon: <HomeOutlined />,
    navLabel: "治理总览",
    navNote: "事件、知识与服务态势",
    headerTag: "总览视图",
    headerTitle: "网格治理态势总览",
    headerNote: "统一查看近 30 天事件趋势、知识覆盖和处置效率，避免在多个模块之间来回切换。"
  },
  {
    key: "/chat",
    icon: <MessageOutlined />,
    navLabel: "智能问答",
    navNote: "RAG 问答与引用核验",
    headerTag: "问答中枢",
    headerTitle: "智能问答与知识引用",
    headerNote: "围绕政策、案例和工单记录进行可追溯问答，帮助一线网格员先查清再答复。"
  },
  {
    key: "/events",
    icon: <AppstoreOutlined />,
    navLabel: "事件协同",
    navNote: "工单受理与处置流转",
    headerTag: "工单协同",
    headerTitle: "事件工单与协同处置",
    headerNote: "集中管理受理、派发、跟进和闭环记录，让高频问题、重点问题和超时风险一眼可见。"
  },
  {
    key: "/knowledge",
    icon: <FileSearchOutlined />,
    navLabel: "知识中枢",
    navNote: "文档上传、索引与追踪",
    headerTag: "知识运营",
    headerTitle: "知识库与检索资产",
    headerNote: "把政策、手册、案例和历史工单沉淀成可检索资产，为问答和研判提供统一底座。"
  },
  {
    key: "/residents",
    icon: <TeamOutlined />,
    navLabel: "居民档案",
    navNote: "重点人群与走访视图",
    headerTag: "人群服务",
    headerTitle: "居民档案与服务跟进",
    headerNote: "聚焦重点人群标签、走访记录和关联事件，形成从人到事、从发现到跟进的闭环。"
  }
];

const weekdayNames = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];

function resolveSection(pathname: string): SectionMeta {
  return sectionItems.find((item) => pathname === item.key || pathname.startsWith(`${item.key}/`)) ?? sectionItems[0];
}

function buildTrail(pathname: string, section: SectionMeta): string[] {
  if (pathname.startsWith("/residents/") && pathname !== "/residents") {
    return [section.navLabel, "服务视图"];
  }

  return ["智能治理管理平台", section.navLabel];
}

export function AppLayout(): JSX.Element {
  const location = useLocation();
  const { collapsed, setCollapsed } = useLayoutStore();

  const currentSection = resolveSection(location.pathname);
  const selectedKey = currentSection.key;
  const trail = buildTrail(location.pathname, currentSection);
  const todayLabel = `${dayjs().format("YYYY年M月D日")} ${weekdayNames[dayjs().day()]}`;

  const menuItems = sectionItems.map((item) => ({
    key: item.key,
    icon: item.icon,
    label: (
      <Link className="app-nav-link" to={item.key}>
        <span className="app-nav-label">{item.navLabel}</span>
        <span className="app-nav-note">{item.navNote}</span>
      </Link>
    )
  }));

  return (
    <Layout className="app-shell">
      <Sider
        width={244}
        collapsedWidth={78}
        collapsed={collapsed}
        trigger={null}
        className="app-sider"
      >
        <div className="layout-brand">
          <div className="layout-brand-mark">治</div>
          {!collapsed ? (
            <div className="layout-brand-copy">
              <div className="layout-brand-title">GridRAG 智能治理管理平台</div>
              <div className="layout-brand-subtitle">网格治理辅助中枢</div>
            </div>
          ) : null}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          theme="dark"
          className="app-nav-menu"
        />
      </Sider>
      <Layout className="app-main">
        <Header className="app-header">
          <div className="app-header-inner">
            <div className="layout-header-main">
              <Button
                type="text"
                aria-label={collapsed ? "展开导航" : "收起导航"}
                className="layout-toggle-btn"
                icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                onClick={() => setCollapsed(!collapsed)}
              />
              <div className="layout-header-copy">
                <div className="layout-header-kicker-row">
                  <span className="layout-header-chip">{currentSection.headerTag}</span>
                  <span className="layout-header-trail">{trail.join(" / ")}</span>
                </div>
                <h2 className="layout-header-title">{currentSection.headerTitle}</h2>
                <p className="layout-header-subtitle">{currentSection.headerNote}</p>
              </div>
            </div>

            <div className="layout-status">
              <div className="layout-date-chip">{todayLabel}</div>
              <div className="layout-operator-card">
                <div className="layout-operator-label">当前值守</div>
                <div className="layout-operator-name">社区网格员</div>
                <div className="layout-operator-state">事件协同与知识问答已就绪</div>
              </div>
            </div>
          </div>
        </Header>
        <Content style={{ paddingTop: 18 }}>
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.38, ease: [0.22, 1, 0.36, 1] }}
          >
            <Outlet />
          </motion.div>
        </Content>
      </Layout>
    </Layout>
  );
}
