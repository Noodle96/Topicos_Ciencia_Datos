import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

export function renderH2CorrelationMatrix({
  containerSelector,
  data,
  onCellClick,
}) {
  const container = d3.select(containerSelector);
  container.selectAll("*").remove();

  const containerNode = container.node();
  const containerWidth = containerNode.clientWidth || 520;
  const containerHeight = containerNode.clientHeight || 360;

  const margin = { top: 44, right: 20, bottom: 60, left: 64 };
  const width = containerWidth - margin.left - margin.right;
  const height = containerHeight - margin.top - margin.bottom;

  const svg = container
    .append("svg")
    .attr("width", containerWidth)
    .attr("height", containerHeight);

  const chart = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const eegChannels = data.eeg_channels;
  const peripheralChannels = data.peripheral_channels;

  const xScale = d3
    .scaleBand()
    .domain(peripheralChannels)
    .range([0, width])
    .padding(0.05);

  const yScale = d3
    .scaleBand()
    .domain(eegChannels)
    .range([0, height])
    .padding(0.05);

  const colorScale = d3
    .scaleSequential()
    .domain([1, -1])
    .interpolator(d3.interpolateRdBu);

  chart
    .selectAll(".h2-cell")
    .data(data.cells)
    .enter()
    .append("rect")
    .attr("class", "h2-cell")
    .attr("x", d => xScale(d.peripheral_channel))
    .attr("y", d => yScale(d.eeg_channel))
    .attr("width", xScale.bandwidth())
    .attr("height", yScale.bandwidth())
    .attr("fill", d =>
      d.correlation === null ? "#e5e7eb" : colorScale(d.correlation)
    )
    .attr("stroke", "#ffffff")
    .attr("cursor", "pointer")
    .on("click", (_, d) => {
      if (onCellClick) {
        onCellClick(d);
      }
    })
    .append("title")
    .text(d => {
      const value =
        d.correlation === null ? "N/A" : d.correlation.toFixed(4);

      return `${d.eeg_channel} × ${d.peripheral_channel}\nPearson: ${value}`;
    });

  chart
    .selectAll(".h2-cell-label")
    .data(data.cells)
    .enter()
    .append("text")
    .attr("class", "h2-cell-label")
    .attr("x", d => xScale(d.peripheral_channel) + xScale.bandwidth() / 2)
    .attr("y", d => yScale(d.eeg_channel) + yScale.bandwidth() / 2)
    .attr("text-anchor", "middle")
    .attr("dominant-baseline", "middle")
    .attr("font-size", "10px")
    .attr("fill", "#111827")
    .style("pointer-events", "none")
    .text(d => {
      if (d.correlation === null) {
        return "";
      }

      return d.correlation.toFixed(2);
    });

  chart
    .append("g")
    .attr("transform", `translate(0, ${height})`)
    .call(d3.axisBottom(xScale));

  chart
    .append("g")
    .call(d3.axisLeft(yScale));

  svg
    .append("text")
    .attr("x", margin.left + width / 2)
    .attr("y", 20)
    .attr("text-anchor", "middle")
    .attr("font-size", "13px")
    .attr("font-weight", "bold")
    .text("Pearson correlation during stimulus");

  svg
    .append("text")
    .attr("x", margin.left + width / 2)
    .attr("y", containerHeight - 12)
    .attr("text-anchor", "middle")
    .attr("font-size", "11px")
    .text("Peripheral signals");

  svg
    .append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -(margin.top + height / 2))
    .attr("y", 16)
    .attr("text-anchor", "middle")
    .attr("font-size", "11px")
    .text("EEG channels");
}