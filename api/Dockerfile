FROM gcc:14.1.0 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        git libsqlite3-dev cmake libasio-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone --depth 1 https://github.com/CrowCpp/Crow.git /crow

COPY main.cpp CMakeLists.txt ./

RUN cmake -DCMAKE_BUILD_TYPE=Release \
          -DCROW_INCLUDE_DIR=/crow/include \
          -S . -B build && \
    cmake --build build --target kalliope_api -j $(nproc)



FROM gcc:14.1.0 AS runtime

# Pull in just the SQLite runtime and CAs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libsqlite3-0 ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the compiled binary
COPY --from=builder /src/build/kalliope_api .

ENV LISTEN_PORT=8080
EXPOSE 8080

CMD ["./kalliope_api"]
