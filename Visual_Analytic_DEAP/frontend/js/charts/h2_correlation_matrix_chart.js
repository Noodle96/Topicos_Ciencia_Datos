export function renderH2CorrelationMatrix({
  containerSelector,
  data,
  onCellClick,
}) {
  const container = d3.select(containerSelector);
  container.selectAll("*").remove();

  const margin = { top: 60, right: 30, bottom: 80, left: 80 };
  const width = 520 - margin.left - margin.right;
  const height = 420 - margin.top - margin.bottom;

  const svg = container
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom);

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
    .domain([-1, 1])
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
      d.correlation === null ? "#ddd" : colorScale(d.correlation)
    )
    .attr("stroke", "#ffffff")
    .attr("cursor", "pointer")
    .on("click", (event, d) => {
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
    .attr("fill", "#111")
    .text(d => {
      if (d.correlation === null) return "";
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
    .attr("y", 25)
    .attr("text-anchor", "middle")
    .attr("font-size", "15px")
    .attr("font-weight", "bold")
    .text("H2 — Correlation Matrix EEG × Peripheral");

  svg
    .append("text")
    .attr("x", margin.left + width / 2)
    .attr("y", height + margin.top + 55)
    .attr("text-anchor", "middle")
    .attr("font-size", "12px")
    .text("Peripheral signals");

  svg
    .append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -(margin.top + height / 2))
    .attr("y", 18)
    .attr("text-anchor", "middle")
    .attr("font-size", "12px")
    .text("EEG channels");
}