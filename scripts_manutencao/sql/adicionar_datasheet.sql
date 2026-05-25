-- Script SQL para adicionar colunas datasheet
-- Execute este script no shell do Render usando: psql $DATABASE_URL

-- Adicionar coluna datasheet em placa_solar (se não existir)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'placa_solar' AND column_name = 'datasheet'
    ) THEN
        ALTER TABLE placa_solar ADD COLUMN datasheet VARCHAR(500);
        RAISE NOTICE '✅ Coluna datasheet adicionada em placa_solar';
    ELSE
        RAISE NOTICE '✅ Coluna datasheet já existe em placa_solar';
    END IF;
END $$;

-- Adicionar coluna datasheet em inversor_solar (se não existir)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'inversor_solar' AND column_name = 'datasheet'
    ) THEN
        ALTER TABLE inversor_solar ADD COLUMN datasheet VARCHAR(500);
        RAISE NOTICE '✅ Coluna datasheet adicionada em inversor_solar';
    ELSE
        RAISE NOTICE '✅ Coluna datasheet já existe em inversor_solar';
    END IF;
END $$;

-- Verificar resultado
SELECT 
    table_name,
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_name IN ('placa_solar', 'inversor_solar')
    AND column_name = 'datasheet';
