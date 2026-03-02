import { app } from "../../../scripts/app.js";

console.log("⦕ Orbitals ⦖ Taggregator extension loaded");

// Helper function to properly hide widgets (enhanced for complete hiding)
function hideWidgetForGood(node, widget, suffix = "") {
  if (!widget) return;

  // Save original properties
  // widget.origType = widget.type;
  // widget.origComputeSize = widget.computeSize;
  // widget.origSerializeValue = widget.serializeValue;

  // Multiple hiding approaches to ensure widget is fully hidden
  widget.computeSize = () => [0, -4]; // -4 compensates for litegraph's automatic widget gap
  widget.type = "converted-widget" + suffix;
  Object.defineProperty(widget, "hidden", {
    value: true,
    writable: false,
  });

  // IMPORTANT: Keep serialization enabled so values are sent to backend
  // (We just hide it visually, but it still needs to send data)

  // Make the widget completely invisible in the DOM if it has element
  if (widget.element) {
    widget.element.style.display = "none";
    widget.element.style.visibility = "hidden";
  }

  // Handle linked widgets recursively
  if (widget.linkedWidgets) {
    for (const w of widget.linkedWidgets) {
      hideWidgetForGood(node, w, ":" + widget.name);
    }
  }
}

app.registerExtension({
  name: "Comfy.Orbitals.Taggregator",

  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "Taggregator") return;

    const onNodeCreated = nodeType.prototype.onNodeCreated;

    function initUI(node, itemsWidget) {
      // Create UI container
      const container = document.createElement("div");
      container.style.cssText = `
                padding: 10px;
                background: rgba(0,0,0,0.3);
                border-radius: 6px;
                margin: 0;
                box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
            `;

      // Fix mousewheel zoom
      container.addEventListener(
        "wheel",
        (e) => {
          const target = e.target;
          if (target.tagName === "TEXTAREA") {
            const hasVerticalScrollbar =
              target.scrollHeight > target.clientHeight;
            if (hasVerticalScrollbar) {
              const atTop = target.scrollTop === 0;
              const atBottom =
                target.scrollTop + target.clientHeight >=
                target.scrollHeight - 1;
              if ((!atTop && e.deltaY < 0) || (!atBottom && e.deltaY > 0)) {
                e.stopPropagation();
              }
            }
          }
        },
        { passive: false },
      );

      const itemsContainer = document.createElement("div");
      itemsContainer.style.cssText =
        "display: flex; flex-direction: column; gap: 10px;";
      container.appendChild(itemsContainer);

      // Update node size
      function updateNodeSize() {
        let totalTextareaHeight = 0;
        itemsContainer.querySelectorAll("textarea").forEach((ta) => {
          totalTextareaHeight += ta.scrollHeight;
        });

        const itemCount =
          itemsContainer.querySelectorAll(".prompt-item").length;
        const calculatedHeight =
          20 +
          itemCount * 60 +
          totalTextareaHeight +
          60 +
          Math.max(0, itemCount - 1) * 10 +
          30;
        const MAX_HEIGHT = 800;
        const height = Math.min(MAX_HEIGHT, Math.max(200, calculatedHeight));

        node.setSize([Math.max(450, node.size[0]), height]);
      }

      // Serialize function
      function serialize() {
        const items = [];
        itemsContainer.querySelectorAll(".prompt-item").forEach((itemElem) => {
          const itemType = itemElem.dataset.type;
          const enabled = itemElem.querySelector(".item-enabled").checked;

          if (itemType === "base") {
            items.push({
              type: "base",
              text: itemElem.querySelector(".base-textarea").value,
              enabled: enabled,
            });
          } else {
            items.push({
              type: "category",
              label: itemElem.querySelector(".tag-label").value,
              tags: itemElem.querySelector(".tag-input").value,
              enabled: enabled,
            });
          }
        });

        node.promptItems = items;
        if (itemsWidget) {
          itemsWidget.value = JSON.stringify(items);
        }
      }

      // Move item up/down
      function moveItem(itemElem, direction) {
        const items = Array.from(
          itemsContainer.querySelectorAll(".prompt-item"),
        );
        const index = items.indexOf(itemElem);

        if (direction === "up" && index > 0) {
          itemsContainer.insertBefore(itemElem, items[index - 1]);
        } else if (direction === "down" && index < items.length - 1) {
          itemsContainer.insertBefore(itemElem, items[index + 2] || null);
        }

        serialize();
        updateArrowStates();
      }

      // Update arrow button states
      function updateArrowStates() {
        const items = Array.from(
          itemsContainer.querySelectorAll(".prompt-item"),
        );
        items.forEach((itemElem, index) => {
          const upBtn = itemElem.querySelector(".move-up");
          const downBtn = itemElem.querySelector(".move-down");

          if (upBtn) {
            upBtn.style.opacity = index === 0 ? "0.3" : "1";
            upBtn.style.cursor = index === 0 ? "not-allowed" : "pointer";
          }

          if (downBtn) {
            downBtn.style.opacity = index === items.length - 1 ? "0.3" : "1";
            downBtn.style.cursor =
              index === items.length - 1 ? "not-allowed" : "pointer";
          }
        });
      }

      // Create base prompt item
      function createBasePromptItem(text = "", enabled = true) {
        const item = document.createElement("div");
        item.className = "prompt-item";
        item.dataset.type = "base";
        item.style.cssText = `
                    padding: 10px;
                    background: rgba(100,150,255,0.08);
                    border: 1px solid rgba(100,150,255,0.2);
                    border-radius: 4px;
                    transition: all 0.3s;
                `;

        // Top row: Label + Move buttons + Checkbox
        const topRow = document.createElement("div");
        topRow.style.cssText = `
                    display: flex;
                    gap: 6px;
                    align-items: center;
                    margin-bottom: 8px;
                `;

        const label = document.createElement("div");
        label.textContent = "Base Prompt";
        label.style.cssText = `
                    flex: 1;
                    color: #aaccff;
                    font-size: 13px;
                    font-weight: 600;
                `;

        // Move up button
        const upBtn = document.createElement("button");
        upBtn.innerHTML = "▲";
        upBtn.className = "move-up";
        upBtn.title = "Move up";
        upBtn.style.cssText = `
                    width: 24px;
                    height: 24px;
                    padding: 0;
                    background: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 3px;
                    color: #aaa;
                    cursor: pointer;
                    font-size: 10px;
                    line-height: 1;
                    transition: all 0.2s;
                    flex-shrink: 0;
                `;
        upBtn.onmouseover = () => {
          if (upBtn.style.cursor === "pointer") {
            upBtn.style.background = "#4a4a4a";
            upBtn.style.color = "#fff";
          }
        };
        upBtn.onmouseout = () => {
          upBtn.style.background = "#3a3a3a";
          upBtn.style.color = "#aaa";
        };
        upBtn.onclick = (e) => {
          e.preventDefault();
          if (upBtn.style.cursor === "pointer") {
            moveItem(item, "up");
          }
        };

        // Move down button
        const downBtn = document.createElement("button");
        downBtn.innerHTML = "▼";
        downBtn.className = "move-down";
        downBtn.title = "Move down";
        downBtn.style.cssText = `
                    width: 24px;
                    height: 24px;
                    padding: 0;
                    background: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 3px;
                    color: #aaa;
                    cursor: pointer;
                    font-size: 10px;
                    line-height: 1;
                    transition: all 0.2s;
                    flex-shrink: 0;
                `;
        downBtn.onmouseover = () => {
          if (downBtn.style.cursor === "pointer") {
            downBtn.style.background = "#4a4a4a";
            downBtn.style.color = "#fff";
          }
        };
        downBtn.onmouseout = () => {
          downBtn.style.background = "#3a3a3a";
          downBtn.style.color = "#aaa";
        };
        downBtn.onclick = (e) => {
          e.preventDefault();
          if (downBtn.style.cursor === "pointer") {
            moveItem(item, "down");
          }
        };

        // Checkbox
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "item-enabled";
        checkbox.checked = enabled;
        checkbox.title = enabled ? "Enabled" : "Disabled";
        checkbox.style.cssText = `
                    width: 22px;
                    height: 22px;
                    cursor: pointer;
                    accent-color: #4a9eff;
                    flex-shrink: 0;
                `;

        topRow.append(label, upBtn, downBtn, checkbox);

        // Textarea
        const textarea = document.createElement("textarea");
        textarea.className = "base-textarea";
        textarea.placeholder =
          "Core description or natural language prompt (e.g., 'A photorealistic portrait of...')";
        textarea.value = text;
        textarea.style.cssText = `
                    width: 100%;
                    padding: 8px 10px;
                    background: #1a1a1a;
                    border: 1px solid #404040;
                    color: #ddd;
                    border-radius: 4px;
                    resize: vertical;
                    min-height: 46px;
                    max-height: 200px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                    line-height: 1.4;
                    outline: none;
                    transition: all 0.2s;
                    box-sizing: border-box;
                    overflow-y: auto;
                `;

        textarea.onfocus = () => {
          textarea.style.borderColor = "#666";
          textarea.style.background = "#222";
        };
        textarea.onblur = () => {
          textarea.style.borderColor = "#404040";
          textarea.style.background = "#1a1a1a";
        };

        textarea.oninput = () => {
          serialize();
          textarea.style.height = "auto";
          textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
          updateNodeSize();
        };

        function updateDisabledState() {
          const isEnabled = checkbox.checked;
          checkbox.title = isEnabled ? "Enabled" : "Disabled";
          item.style.opacity = isEnabled ? "1" : "0.4";
          item.style.background = isEnabled
            ? "rgba(100,150,255,0.08)"
            : "rgba(0,0,0,0.2)";
          textarea.style.color = isEnabled ? "#ddd" : "#666";
        }

        checkbox.onchange = () => {
          updateDisabledState();
          serialize();
        };

        item.appendChild(topRow);
        item.appendChild(textarea);

        setTimeout(() => {
          textarea.style.height = "auto";
          textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
          updateDisabledState();
        }, 0);

        return item;
      }

      // Create category item
      function createCategoryItem(label = "", tags = "", enabled = true) {
        const item = document.createElement("div");
        item.className = "prompt-item";
        item.dataset.type = "category";
        item.style.cssText = `
                    padding: 10px;
                    background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 4px;
                    transition: all 0.3s;
                `;

        // Top row
        const topRow = document.createElement("div");
        topRow.style.cssText = `
                    display: flex;
                    gap: 6px;
                    align-items: center;
                    margin-bottom: 8px;
                `;

        // Label input
        const labelInput = document.createElement("input");
        labelInput.className = "tag-label";
        labelInput.placeholder = "Category name (e.g., 'Style', 'Quality')";
        labelInput.value = label;
        labelInput.style.cssText = `
                    flex: 1;
                    padding: 6px 10px;
                    background: #1a1a1a;
                    border: 1px solid #404040;
                    color: #fff;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: 500;
                    font-family: sans-serif;
                    outline: none;
                    transition: all 0.2s;
                `;
        labelInput.onfocus = () => {
          labelInput.style.borderColor = "#666";
          labelInput.style.background = "#222";
        };
        labelInput.onblur = () => {
          labelInput.style.borderColor = "#404040";
          labelInput.style.background = "#1a1a1a";
        };

        // Move up button
        const upBtn = document.createElement("button");
        upBtn.innerHTML = "▲";
        upBtn.className = "move-up";
        upBtn.title = "Move up";
        upBtn.style.cssText = `
                    width: 24px;
                    height: 24px;
                    padding: 0;
                    background: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 3px;
                    color: #aaa;
                    cursor: pointer;
                    font-size: 10px;
                    line-height: 1;
                    transition: all 0.2s;
                    flex-shrink: 0;
                `;
        upBtn.onmouseover = () => {
          if (upBtn.style.cursor === "pointer") {
            upBtn.style.background = "#4a4a4a";
            upBtn.style.color = "#fff";
          }
        };
        upBtn.onmouseout = () => {
          upBtn.style.background = "#3a3a3a";
          upBtn.style.color = "#aaa";
        };
        upBtn.onclick = (e) => {
          e.preventDefault();
          if (upBtn.style.cursor === "pointer") {
            moveItem(item, "up");
          }
        };

        // Move down button
        const downBtn = document.createElement("button");
        downBtn.innerHTML = "▼";
        downBtn.className = "move-down";
        downBtn.title = "Move down";
        downBtn.style.cssText = `
                    width: 24px;
                    height: 24px;
                    padding: 0;
                    background: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 3px;
                    color: #aaa;
                    cursor: pointer;
                    font-size: 10px;
                    line-height: 1;
                    transition: all 0.2s;
                    flex-shrink: 0;
                `;
        downBtn.onmouseover = () => {
          if (downBtn.style.cursor === "pointer") {
            downBtn.style.background = "#4a4a4a";
            downBtn.style.color = "#fff";
          }
        };
        downBtn.onmouseout = () => {
          downBtn.style.background = "#3a3a3a";
          downBtn.style.color = "#aaa";
        };
        downBtn.onclick = (e) => {
          e.preventDefault();
          if (downBtn.style.cursor === "pointer") {
            moveItem(item, "down");
          }
        };

        // Checkbox
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "item-enabled";
        checkbox.checked = enabled;
        checkbox.title = enabled ? "Enabled" : "Disabled";
        checkbox.style.cssText = `
                    width: 22px;
                    height: 22px;
                    cursor: pointer;
                    accent-color: #4a9eff;
                    flex-shrink: 0;
                `;

        // Remove button
        const removeBtn = document.createElement("button");
        removeBtn.innerHTML = "×";
        removeBtn.title = "Remove category";
        removeBtn.style.cssText = `
                    width: 28px;
                    height: 28px;
                    padding: 0;
                    background: #d44;
                    border: none;
                    border-radius: 4px;
                    color: #fff;
                    cursor: pointer;
                    font-size: 20px;
                    font-weight: bold;
                    line-height: 1;
                    transition: all 0.2s;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
                    flex-shrink: 0;
                `;
        removeBtn.onmouseover = () => {
          removeBtn.style.background = "#e55";
          removeBtn.style.transform = "scale(1.1)";
        };
        removeBtn.onmouseout = () => {
          removeBtn.style.background = "#d44";
          removeBtn.style.transform = "scale(1)";
        };
        removeBtn.onclick = () => {
          item.style.opacity = "0";
          item.style.transform = "translateX(-10px)";
          setTimeout(() => {
            item.remove();
            serialize();
            updateNodeSize();
            updateArrowStates();
          }, 200);
        };

        topRow.append(labelInput, upBtn, downBtn, checkbox, removeBtn);

        // Tags textarea
        const tagInput = document.createElement("textarea");
        tagInput.className = "tag-input";
        tagInput.placeholder =
          "Comma-separated tags OR natural language - your choice! (e.g., 'masterpiece, 8k' OR 'high quality photo')";
        tagInput.value = tags;
        tagInput.style.cssText = `
                    width: 100%;
                    padding: 8px 10px;
                    background: #1a1a1a;
                    border: 1px solid #404040;
                    color: #ddd;
                    border-radius: 4px;
                    resize: vertical;
                    min-height: 46px;
                    max-height: 200px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                    line-height: 1.4;
                    outline: none;
                    transition: all 0.2s;
                    box-sizing: border-box;
                    overflow-y: auto;
                `;
        tagInput.onfocus = () => {
          tagInput.style.borderColor = "#666";
          tagInput.style.background = "#222";
        };
        tagInput.onblur = () => {
          tagInput.style.borderColor = "#404040";
          tagInput.style.background = "#1a1a1a";
        };

        tagInput.oninput = () => {
          serialize();
          tagInput.style.height = "auto";
          tagInput.style.height = Math.min(tagInput.scrollHeight, 200) + "px";
          updateNodeSize();
        };

        function updateDisabledState() {
          const isEnabled = checkbox.checked;
          checkbox.title = isEnabled ? "Enabled" : "Disabled";
          item.style.opacity = isEnabled ? "1" : "0.4";
          item.style.background = isEnabled
            ? "rgba(255,255,255,0.03)"
            : "rgba(0,0,0,0.2)";
          labelInput.style.color = isEnabled ? "#fff" : "#888";
          labelInput.style.fontStyle = isEnabled ? "normal" : "italic";
          tagInput.style.color = isEnabled ? "#ddd" : "#666";
        }

        checkbox.onchange = () => {
          updateDisabledState();
          serialize();
        };

        [labelInput, checkbox].forEach((el) => {
          el.onchange = serialize;
        });

        item.appendChild(topRow);
        item.appendChild(tagInput);

        setTimeout(() => {
          tagInput.style.height = "auto";
          tagInput.style.height = Math.min(tagInput.scrollHeight, 200) + "px";
          updateDisabledState();
        }, 0);

        // Animate in
        item.style.opacity = "0";
        item.style.transform = "translateY(-10px)";
        setTimeout(() => {
          updateDisabledState();
          item.style.transform = "translateY(0)";
        }, 10);

        return item;
      }

      // Add category button
      const addBtn = document.createElement("button");
      addBtn.innerHTML = "+ Add Category";
      addBtn.style.cssText = `
                width: 100%;
                padding: 10px;
                margin-top: 10px;
                background: linear-gradient(180deg, #4a4a4a 0%, #3a3a3a 100%);
                border: 1px solid #555;
                border-radius: 4px;
                color: #fff;
                cursor: pointer;
                font-size: 13px;
                font-weight: 600;
                transition: all 0.2s;
                box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            `;
      addBtn.onmouseover = () => {
        addBtn.style.background =
          "linear-gradient(180deg, #5a5a5a 0%, #4a4a4a 100%)";
        addBtn.style.borderColor = "#666";
        addBtn.style.transform = "translateY(-1px)";
        addBtn.style.boxShadow = "0 2px 5px rgba(0,0,0,0.4)";
      };
      addBtn.onmouseout = () => {
        addBtn.style.background =
          "linear-gradient(180deg, #4a4a4a 0%, #3a3a3a 100%)";
        addBtn.style.borderColor = "#555";
        addBtn.style.transform = "translateY(0)";
        addBtn.style.boxShadow = "0 1px 3px rgba(0,0,0,0.3)";
      };
      addBtn.onclick = () => {
        const newItem = createCategoryItem();
        itemsContainer.appendChild(newItem);
        serialize();
        updateNodeSize();
        updateArrowStates();
      };

      container.appendChild(addBtn);

      // Load saved items
      if (node.promptItems && node.promptItems.length > 0) {
        node.promptItems.forEach((itemData) => {
          let itemElem;
          if (itemData.type === "base") {
            itemElem = createBasePromptItem(
              itemData.text || "",
              itemData.enabled !== false,
            );
          } else {
            itemElem = createCategoryItem(
              itemData.label || "",
              itemData.tags || "",
              itemData.enabled !== false,
            );
          }
          itemsContainer.appendChild(itemElem);
        });
      }

      // Add to node
      node.addDOMWidget("taggregator_ui", "div", container, {
        serialize: false,
        hideOnZoom: false,
      });

      // Serialize initial state and update UI
      serialize();

      // Initial size and arrow states
      setTimeout(() => {
        updateNodeSize();
        updateArrowStates();
      }, 100);
    }

    nodeType.prototype.onNodeCreated = function () {
      const r = onNodeCreated
        ? onNodeCreated.apply(this, arguments)
        : undefined;

      // Store ordered items: [{type: "base", text: "...", enabled: true}, {type: "category", label: "...", tags: "...", enabled: true}]
      this.promptItems = this.promptItems || [
        { type: "base", text: "", enabled: true }, // Base prompt starts enabled
        { type: "category", label: "", tags: "", enabled: true }, // One empty category
      ];

      // Hide the default widget
      const itemsWidget = this.widgets?.find(
        (w) => w.name === "prompt_items_json",
      );
      if (itemsWidget) {
        hideWidgetForGood(this, itemsWidget);
      }

      // Build the custom DOM UI once per node instance
      if (!this._taggregator_ui_initialized) {
        this._taggregator_ui_initialized = true;
        initUI(this, itemsWidget);
      }

      return r;
    };

    // Serialize
    const onSerialize = nodeType.prototype.onSerialize;
    nodeType.prototype.onSerialize = function (o) {
      onSerialize?.apply(this, arguments);
      if (this.promptItems) {
        o.promptItems = this.promptItems;
      }
    };

    // Deserialize
    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function (o) {
      if (onConfigure) {
        onConfigure.apply(this, arguments);
      }
      if (o.promptItems) {
        this.promptItems = o.promptItems;
      }
    };
  },
});
