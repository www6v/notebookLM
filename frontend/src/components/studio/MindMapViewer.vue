<template>
  <div class="mindmap-viewer">
    <div class="mindmap-header">
      <span class="mindmap-title">{{ title }}</span>
    </div>
    <div
      v-if="treeRoot"
      ref="containerRef"
      class="mindmap-canvas"
      :class="{ 'mindmap-canvas--fullscreen': fullscreen }"
    >
      <svg class="mindmap-svg" :viewBox="svgViewBox">
        <!-- Edges -->
        <path
          v-for="(edge, idx) of edgePaths"
          :key="'e' + idx"
          :d="edge.d"
          class="mindmap-edge"
        />
        <!-- Nodes -->
        <g
          v-for="node of layoutNodes"
          :key="node.id"
          :transform="`translate(${node.x}, ${node.y})`"
          class="mindmap-node"
        >
          <rect
            :x="-node.width / 2"
            :y="-node.height / 2"
            :width="node.width"
            :height="node.height"
            :rx="node.depth === 0 ? 20 : 12"
            :class="['node-rect', `depth-${Math.min(node.depth, 3)}`]"
          />
          <text
            dy="0.35em"
            text-anchor="middle"
            :class="['node-label', `depth-${Math.min(node.depth, 3)}`]"
          >
            {{ node.label }}
          </text>
        </g>
      </svg>
    </div>
    <div v-else class="mindmap-empty">
      <p>No mind map data available.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface GraphNode {
  id: string
  label: string
}

interface GraphEdge {
  source: string
  target: string
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

interface TreeNode {
  id: string
  label: string
  children: TreeNode[]
}

interface LayoutNode {
  id: string
  label: string
  x: number
  y: number
  width: number
  height: number
  depth: number
}

interface EdgePath {
  d: string
}

const props = withDefaults(defineProps<{
  graphData: GraphData | null
  title: string
  fullscreen?: boolean
}>(), {
  fullscreen: false,
})

const containerRef = ref<HTMLDivElement | null>(null)

const NODE_H_GAP = 60
const NODE_V_GAP = 16
const NODE_HEIGHT = 36
const CHAR_WIDTH = 8
const NODE_PADDING = 24

const getNodeWidth = (label: string): number => {
  return Math.max(80, label.length * CHAR_WIDTH + NODE_PADDING * 2)
}

const treeRoot = computed<TreeNode | null>(() => {
  if (!props.graphData || !props.graphData.nodes || props.graphData.nodes.length === 0) {
    return null
  }

  const { nodes, edges } = props.graphData
  const childSet = new Set(edges.map((e) => e.target))
  const nodeMap = new Map<string, TreeNode>()

  for (const n of nodes) {
    nodeMap.set(n.id, { id: n.id, label: n.label, children: [] })
  }

  for (const e of edges) {
    const parent = nodeMap.get(e.source)
    const child = nodeMap.get(e.target)
    if (parent && child) {
      parent.children.push(child)
    }
  }

  let rootId = nodes.find((n) => !childSet.has(n.id))?.id
  if (!rootId) {
    rootId = nodes[0].id
  }

  return nodeMap.get(rootId) || null
})

const computeSubtreeHeight = (node: TreeNode): number => {
  if (node.children.length === 0) {
    return NODE_HEIGHT
  }
  let total = 0
  for (const child of node.children) {
    total += computeSubtreeHeight(child)
  }
  total += (node.children.length - 1) * NODE_V_GAP
  return Math.max(NODE_HEIGHT, total)
}

const layoutResult = computed(() => {
  if (!treeRoot.value) {
    return { nodes: [] as LayoutNode[], edges: [] as EdgePath[], width: 0, height: 0 }
  }

  const allNodes: LayoutNode[] = []
  const allEdges: EdgePath[] = []

  const layoutSubtree = (
    node: TreeNode,
    x: number,
    yStart: number,
    depth: number,
  ): { centerY: number } => {
    const nodeWidth = getNodeWidth(node.label)

    if (node.children.length === 0) {
      const cy = yStart + NODE_HEIGHT / 2
      allNodes.push({
        id: node.id,
        label: node.label,
        x,
        y: cy,
        width: nodeWidth,
        height: NODE_HEIGHT,
        depth,
      })
      return { centerY: cy }
    }

    const childX = x + nodeWidth / 2 + NODE_H_GAP + getNodeWidth(node.children[0].label) / 2

    let currentY = yStart
    const childCenters: number[] = []

    for (const child of node.children) {
      const childH = computeSubtreeHeight(child)
      const childNodeWidth = getNodeWidth(child.label)
      const adjustedX = x + nodeWidth / 2 + NODE_H_GAP + childNodeWidth / 2
      const result = layoutSubtree(child, adjustedX, currentY, depth + 1)
      childCenters.push(result.centerY)
      currentY += childH + NODE_V_GAP
    }

    const firstCenter = childCenters[0]
    const lastCenter = childCenters[childCenters.length - 1]
    const cy = (firstCenter + lastCenter) / 2

    allNodes.push({
      id: node.id,
      label: node.label,
      x,
      y: cy,
      width: nodeWidth,
      height: NODE_HEIGHT,
      depth,
    })

    for (let i = 0; i < node.children.length; i++) {
      const childNode = allNodes.find((n) => n.id === node.children[i].id)
      if (childNode) {
        const startX = x + nodeWidth / 2
        const endX = childNode.x - childNode.width / 2
        const midX = (startX + endX) / 2
        allEdges.push({
          d: `M ${startX} ${cy} C ${midX} ${cy}, ${midX} ${childCenters[i]}, ${endX} ${childCenters[i]}`,
        })
      }
    }

    return { centerY: cy }
  }

  const rootWidth = getNodeWidth(treeRoot.value.label)
  const totalH = computeSubtreeHeight(treeRoot.value)
  const startX = rootWidth / 2 + 20
  layoutSubtree(treeRoot.value, startX, 20, 0)

  let maxX = 0
  for (const n of allNodes) {
    const right = n.x + n.width / 2
    if (right > maxX) {
      maxX = right
    }
  }

  return {
    nodes: allNodes,
    edges: allEdges,
    width: maxX + 40,
    height: totalH + 40,
  }
})

const layoutNodes = computed(() => layoutResult.value.nodes)
const edgePaths = computed(() => layoutResult.value.edges)
const svgViewBox = computed(
  () => `0 0 ${layoutResult.value.width} ${layoutResult.value.height}`
)
</script>

<style scoped>
.mindmap-viewer {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mindmap-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.mindmap-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #333);
}

.mindmap-canvas {
  border: 1px solid var(--border-color, #e8eaed);
  border-radius: 8px;
  background: #fafbfc;
  overflow: auto;
  min-height: 200px;
  max-height: 500px;
}

.mindmap-canvas--fullscreen {
  max-height: 75vh;
  min-height: 400px;
}

.mindmap-svg {
  width: 100%;
  height: auto;
  min-height: 200px;
}

.mindmap-edge {
  fill: none;
  stroke: #b0bec5;
  stroke-width: 1.5;
}

.node-rect {
  stroke-width: 1.5;
  cursor: default;
}

.node-rect.depth-0 {
  fill: #4285f4;
  stroke: #3367d6;
}

.node-rect.depth-1 {
  fill: #34a853;
  stroke: #2d8e47;
}

.node-rect.depth-2 {
  fill: #fbbc04;
  stroke: #e0a800;
}

.node-rect.depth-3 {
  fill: #ea4335;
  stroke: #d33426;
}

.node-label {
  font-size: 12px;
  pointer-events: none;
  user-select: none;
}

.node-label.depth-0 {
  fill: #fff;
  font-weight: 600;
}

.node-label.depth-1 {
  fill: #fff;
  font-weight: 500;
}

.node-label.depth-2 {
  fill: #333;
  font-weight: 500;
}

.node-label.depth-3 {
  fill: #fff;
  font-weight: 500;
}

.mindmap-empty {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-secondary, #888);
  font-size: 13px;
}
</style>
